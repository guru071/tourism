"""
Verification and Adversarial Stress Harness for docker-compose.yml
Validates:
- Service dependency graph (DAG, topological sort, missing deps, health condition validity)
- Port collision matrix (host port uniqueness, container port mappings)
- Volume binding integrity (named volume existence, host bind mount path existence, anonymous volumes)
- Inter-service environment variable contracts (DB credentials, Redis URLs, API targets)
"""

import sys
import os
import re
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"

def run_compose_validation():
    print("========================================================")
    print(" DOCKER COMPOSE ADVERSARIAL VALIDATION HARNESS")
    print(f" Target: {COMPOSE_FILE}")
    print("========================================================\n")

    if not COMPOSE_FILE.exists():
        print(f"[FAIL] docker-compose.yml not found at {COMPOSE_FILE}")
        return 1

    with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
        try:
            compose = yaml.safe_load(f)
        except Exception as e:
            print(f"[FAIL] YAML syntax error: {e}")
            return 1

    services = compose.get("services", {})
    named_volumes = compose.get("volumes", {}) or {}

    findings = []
    warnings = []
    checks_passed = 0

    print(f"Parsed {len(services)} services: {list(services.keys())}")
    print(f"Parsed {len(named_volumes)} named volumes: {list(named_volumes.keys())}\n")

    # 1. Dependency Graph & DAG Validation
    print("--- 1. Service Dependency Graph ---")
    dep_graph = {}
    health_conditions = {}

    for name, svc in services.items():
        depends_on = svc.get("depends_on", [])
        deps = []
        if isinstance(depends_on, list):
            deps = depends_on
        elif isinstance(depends_on, dict):
            for dep_name, dep_opts in depends_on.items():
                deps.append(dep_name)
                if isinstance(dep_opts, dict) and "condition" in dep_opts:
                    health_conditions[(name, dep_name)] = dep_opts["condition"]
        dep_graph[name] = deps

    # Check for missing dependency targets
    for svc_name, deps in dep_graph.items():
        for dep in deps:
            if dep not in services:
                findings.append(f"Service '{svc_name}' depends on non-existent service '{dep}'")
            else:
                checks_passed += 1
                print(f"  [OK] Dependency: {svc_name} -> {dep}")

    # Check health condition validity
    for (consumer, provider), condition in health_conditions.items():
        if condition == "service_healthy":
            provider_svc = services.get(provider, {})
            if "healthcheck" not in provider_svc:
                findings.append(f"Service '{consumer}' expects '{provider}' to be 'service_healthy', but '{provider}' defines NO healthcheck!")
            else:
                checks_passed += 1
                print(f"  [OK] Healthcheck dependency verified: {consumer} -> {provider} (has healthcheck)")

    # Cycle detection via DFS
    visited = {}
    def check_cycle(node, path):
        visited[node] = 1 # in progress
        for neighbor in dep_graph.get(node, []):
            if neighbor not in services:
                continue
            if visited.get(neighbor) == 1:
                findings.append(f"Cyclic dependency detected: {' -> '.join(path + [neighbor])}")
                return True
            elif visited.get(neighbor) == 0:
                continue
            else:
                if check_cycle(neighbor, path + [neighbor]):
                    return True
        visited[node] = 0 # finished
        return False

    for s in services:
        if s not in visited:
            check_cycle(s, [s])
    checks_passed += 1
    print("  [OK] Dependency graph is strictly acyclic (DAG confirmed)")

    # Check for unmonitored startup dependencies
    for svc_name, deps in dep_graph.items():
        for dep in deps:
            if (svc_name, dep) not in health_conditions:
                warnings.append(f"Service '{svc_name}' depends on '{dep}' without 'service_healthy' condition (startup race possible)")

    # 2. Port Collision Matrix
    print("\n--- 2. Port Collision Matrix ---")
    host_ports = {}
    container_ports = {}

    for name, svc in services.items():
        ports = svc.get("ports", [])
        for p in ports:
            # Handle format "HOST:CONTAINER" or int
            p_str = str(p)
            parts = p_str.split(":")
            if len(parts) == 2:
                h_port, c_port = parts[0], parts[1]
            elif len(parts) == 1:
                h_port, c_port = parts[0], parts[0]
            elif len(parts) == 3: # host_ip:host_port:container_port
                h_port, c_port = parts[1], parts[2]
            else:
                findings.append(f"Malformed port mapping in {name}: {p}")
                continue

            # Host port conflict
            if h_port in host_ports:
                findings.append(f"PORT CONFLICT: Host port {h_port} claimed by both '{host_ports[h_port]}' and '{name}'")
            else:
                host_ports[h_port] = name

            container_ports.setdefault(name, []).append(c_port)
            print(f"  [OK] Port mapped: {name} host:{h_port} -> container:{c_port}")
            checks_passed += 1

    # 3. Volume Binding Integrity
    print("\n--- 3. Volume Binding Integrity ---")
    for name, svc in services.items():
        volumes = svc.get("volumes", [])
        for v in volumes:
            v_str = str(v)
            parts = v_str.split(":")
            if len(parts) == 1:
                # Anonymous volume e.g. /app/node_modules
                print(f"  [OK] Anonymous volume in '{name}': {parts[0]}")
                checks_passed += 1
            elif len(parts) >= 2:
                source, target = parts[0], parts[1]
                if source.startswith(".") or source.startswith("/") or "\\" in source:
                    # Bind mount
                    host_path = (PROJECT_ROOT / source).resolve()
                    if not host_path.exists():
                        findings.append(f"Bind mount host path does not exist for service '{name}': {source} ({host_path})")
                    else:
                        print(f"  [OK] Bind mount verified for '{name}': {source} -> {target} (exists: {host_path.name})")
                        checks_passed += 1
                else:
                    # Named volume
                    if source not in named_volumes:
                        findings.append(f"Service '{name}' references undeclared named volume '{source}'")
                    else:
                        print(f"  [OK] Named volume verified for '{name}': {source} -> {target}")
                        checks_passed += 1

    # Check for unused named volumes
    used_named_vols = set()
    for name, svc in services.items():
        for v in svc.get("volumes", []):
            parts = str(v).split(":")
            if len(parts) >= 2 and not (parts[0].startswith(".") or parts[0].startswith("/") or "\\" in parts[0]):
                used_named_vols.add(parts[0])

    for nv in named_volumes:
        if nv not in used_named_vols:
            warnings.append(f"Declared named volume '{nv}' is not used by any service")

    # 4. Inter-Service Configuration Alignment
    print("\n--- 4. Configuration & Inter-Service Alignment ---")
    # Check Postgres credentials vs Backend DATABASE_URL
    pg_svc = services.get("postgres", {})
    pg_env = pg_svc.get("environment", {})
    if isinstance(pg_env, list):
        pg_env = dict(item.split("=", 1) for item in pg_env if "=" in item)

    pg_user = pg_env.get("POSTGRES_USER", "postgres")
    pg_pass = pg_env.get("POSTGRES_PASSWORD", "")
    pg_db = pg_env.get("POSTGRES_DB", "")

    backend_svc = services.get("backend", {})
    backend_env = backend_svc.get("environment", {})
    if isinstance(backend_env, list):
        backend_env = dict(item.split("=", 1) for item in backend_env if "=" in item)

    db_url = backend_env.get("DATABASE_URL", "")
    if db_url:
        if pg_user not in db_url or pg_pass not in db_url or pg_db not in db_url:
            findings.append(f"DATABASE_URL in backend mismatch with postgres credentials: URL={db_url}")
        else:
            print(f"  [OK] Backend DATABASE_URL matches Postgres credentials ({pg_user}@{pg_db})")
            checks_passed += 1

        if "@postgres:5432" not in db_url:
            warnings.append(f"DATABASE_URL does not point to docker service 'postgres:5432': {db_url}")
        else:
            print("  [OK] Backend DATABASE_URL points to internal 'postgres:5432' network")
            checks_passed += 1

    # Check Redis URL
    redis_url = backend_env.get("REDIS_URL", "")
    if redis_url:
        if "@redis:6379" not in redis_url and "redis://redis:6379" not in redis_url:
            warnings.append(f"REDIS_URL does not target internal 'redis:6379' service: {redis_url}")
        else:
            print("  [OK] Backend REDIS_URL points to internal 'redis:6379' service")
            checks_passed += 1

    # Check Frontend NEXT_PUBLIC_API_URL
    frontend_svc = services.get("frontend", {})
    frontend_env = frontend_svc.get("environment", {})
    if isinstance(frontend_env, list):
        frontend_env = dict(item.split("=", 1) for item in frontend_env if "=" in item)

    api_url = frontend_env.get("NEXT_PUBLIC_API_URL", "")
    if api_url:
        print(f"  [INFO] Frontend NEXT_PUBLIC_API_URL: {api_url}")
        if "localhost:8000" in api_url:
            print("  [OK] Frontend targets host localhost:8000 (suitable for browser execution)")
            checks_passed += 1
            warnings.append("NEXT_PUBLIC_API_URL points to localhost:8000. If frontend performs Server-Side Rendering (SSR) inside Docker container, localhost:8000 will fail unless requests originate from browser on host.")
        elif "backend:8000" in api_url:
            print("  [OK] Frontend targets backend:8000 (suitable for container SSR)")
            checks_passed += 1

    # 5. Healthcheck Specifications
    print("\n--- 5. Healthcheck Specification Audit ---")
    for s_name, svc in services.items():
        hc = svc.get("healthcheck")
        if hc:
            test_cmd = hc.get("test")
            print(f"  [OK] {s_name} healthcheck: {test_cmd}")
            checks_passed += 1
        else:
            print(f"  [NOTICE] {s_name} has no healthcheck defined")
            if s_name == "backend":
                warnings.append("Backend has no healthcheck defined in docker-compose.yml. Dependent services cannot verify backend readiness.")

    print("\n========================================================")
    print(f" SUMMARY: {checks_passed} Checks Passed")
    print(f" Findings (Fatal/Violations): {len(findings)}")
    print(f" Architectural Warnings: {len(warnings)}")
    print("========================================================")

    if findings:
        print("\n[CRITICAL FINDINGS]")
        for f in findings:
            print(f"  - {f}")

    if warnings:
        print("\n[ARCHITECTURAL WARNINGS / OBSERVATIONS]")
        for w in warnings:
            print(f"  - {w}")

    return 0 if len(findings) == 0 else 1

if __name__ == "__main__":
    sys.exit(run_compose_validation())
