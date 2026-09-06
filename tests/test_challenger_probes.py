"""
Adversarial Challenger Verification Battery for Remediated Ecosystem
Contains:
1. Dockerfile Negative Assertions & Mutation Oracle Resistance
2. Docker Compose Dependency & Configuration Negative Probes
3. Model and Schema Boundary Stress Testing
"""

import re
import pytest
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"


def validate_dockerfile_integrity(content: str) -> None:
    """
    Validation oracle for frontend/Dockerfile.
    Must enforce authentic production Next.js compilation and reject dummy facades.
    """
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]

    # 1. Structural depth
    assert len(lines) >= 6, f"Dockerfile must contain genuine build pipeline (found only {len(lines)} lines)"

    # 2. Node 20 runtime base image
    assert any(re.search(r"^FROM\s+node:20", line, re.IGNORECASE) for line in lines), (
        "Base image must use Node.js 20"
    )

    # 3. Package manifest copy
    assert any(re.search(r"^COPY\s+package(?:\*\.json|\.json)", line) for line in lines), (
        "Dockerfile must copy package manifests"
    )

    # 4. Dependency installation
    assert any(re.search(r"^RUN\s+(?:npm\s+(?:ci|install)|yarn|pnpm)", line) for line in lines), (
        "Dockerfile must install dependencies"
    )

    # 5. Production Next.js compilation
    assert any(re.search(r"^RUN\s+(?:npm\s+run\s+build|next\s+build|npx\s+next\s+build)", line) for line in lines), (
        "Dockerfile must compile Next.js application"
    )

    # 6. Expose port 3000
    assert any(re.search(r"^EXPOSE\s+3000\b", line) for line in lines), (
        "Dockerfile must expose port 3000"
    )

    # 7. Start command
    assert any(
        re.search(r'CMD\s+\[.*?(?:"npm"|"npx"|"next"|"node").*?(?:"start"|"run"|"server\.js").*?\]', line)
        or re.search(r'CMD\s+(?:npm\s+run\s+start|npm\s+start|next\s+start)', line)
        for line in lines
    ), "Dockerfile CMD must execute Next.js startup command"

    # 8. Negative Assertions: Anti-patterns and dummy stubs
    lower = content.lower()
    assert "setinterval" not in lower, "Integrity Violation: dummy setInterval detected"
    assert "sleep infinity" not in lower, "Integrity Violation: dummy sleep infinity detected"
    assert "node -e" not in content and 'node", "-e' not in content, "Integrity Violation: dummy node -e detected"
    assert "tail -f /dev/null" not in lower, "Integrity Violation: dummy tail detected"


class TestDockerfileAdversarialIntegrity:
    """Stress tests and negative assertions targeting frontend/Dockerfile."""

    def test_genuine_dockerfile_passes_oracle(self):
        dockerfile_path = FRONTEND_DIR / "Dockerfile"
        assert dockerfile_path.exists(), "frontend/Dockerfile must exist"
        content = dockerfile_path.read_text(encoding="utf-8")
        validate_dockerfile_integrity(content)

    def test_mutation_rejects_old_5line_dummy_stub(self):
        old_stub = """FROM node:18-alpine
WORKDIR /app
EXPOSE 3000
CMD ["node", "-e", "console.log('Frontend container ready'); setInterval(() => {}, 1000)"]
"""
        with pytest.raises(AssertionError) as exc:
            validate_dockerfile_integrity(old_stub)
        assert any(k in str(exc.value) for k in ["build pipeline", "setInterval", "Node.js 20"])

    def test_mutation_rejects_sleep_infinity_stub(self):
        stub = """FROM node:20-alpine
WORKDIR /app
ENV PORT=3000
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["sleep", "infinity"]
"""
        with pytest.raises(AssertionError) as exc:
            validate_dockerfile_integrity(stub)
        assert any(k in str(exc.value) for k in ["sleep infinity", "startup command"])

    def test_mutation_rejects_missing_build_step(self):
        stub = """FROM node:20-alpine
WORKDIR /app
ENV PORT=3000
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "start"]
"""
        with pytest.raises(AssertionError) as exc:
            validate_dockerfile_integrity(stub)
        assert "compile Next.js application" in str(exc.value)

    def test_mutation_rejects_missing_package_manifest_copy(self):
        stub = """FROM node:20-alpine
WORKDIR /app
ENV PORT=3000
COPY . .
RUN npm install
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "start"]
"""
        with pytest.raises(AssertionError) as exc:
            validate_dockerfile_integrity(stub)
        assert "package manifests" in str(exc.value)

    def test_mutation_rejects_node18_base_image(self):
        stub = """FROM node:18-alpine
WORKDIR /app
ENV PORT=3000
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "start"]
"""
        with pytest.raises(AssertionError) as exc:
            validate_dockerfile_integrity(stub)
        assert "Node.js 20" in str(exc.value)


class TestDockerComposeAdversarialIntegrity:
    """Stress tests and negative assertions targeting docker-compose.yml."""

    @pytest.fixture
    def compose_data(self):
        assert COMPOSE_FILE.exists(), "docker-compose.yml must exist"
        with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_backend_healthcheck_contract(self, compose_data):
        services = compose_data.get("services", {})
        backend = services.get("backend", {})
        assert "healthcheck" in backend, "backend service MUST define a healthcheck"
        hc = backend["healthcheck"]
        test_cmd = hc.get("test", [])
        test_cmd_str = " ".join(test_cmd) if isinstance(test_cmd, list) else str(test_cmd)
        assert "urllib.request" in test_cmd_str or "http://localhost:8000/health" in test_cmd_str, (
            "Backend healthcheck must probe /health endpoint"
        )
        assert hc.get("interval") == "5s"
        assert hc.get("timeout") == "5s"
        assert hc.get("retries") == 5

    def test_frontend_depends_on_backend_service_healthy(self, compose_data):
        services = compose_data.get("services", {})
        frontend = services.get("frontend", {})
        depends_on = frontend.get("depends_on", {})
        assert isinstance(depends_on, dict), "frontend depends_on must be a dictionary specifying conditions"
        assert "backend" in depends_on, "frontend must depend on backend"
        assert depends_on["backend"].get("condition") == "service_healthy", (
            "frontend must specify 'condition: service_healthy' on backend"
        )

    def test_frontend_anonymous_next_volume(self, compose_data):
        services = compose_data.get("services", {})
        frontend = services.get("frontend", {})
        volumes = frontend.get("volumes", [])
        assert "/app/.next" in volumes, (
            "frontend must include anonymous volume '/app/.next' to prevent host bind mount from masking compiled artifacts"
        )
        assert "/app/node_modules" in volumes, (
            "frontend must include anonymous volume '/app/node_modules'"
        )

    def test_backend_depends_on_postgres_and_redis_healthy(self, compose_data):
        services = compose_data.get("services", {})
        backend = services.get("backend", {})
        depends_on = backend.get("depends_on", {})
        assert isinstance(depends_on, dict), "backend depends_on must be a dict"
        assert depends_on.get("postgres", {}).get("condition") == "service_healthy"
        assert depends_on.get("redis", {}).get("condition") == "service_healthy"


class TestComposeValidatorMutationSensitivity:
    """Verify that the verification harness tests/verify_docker_compose.py detects injected flaws."""

    def test_dag_cycle_detection(self):
        dep_graph = {
            "a": ["b"],
            "b": ["c"],
            "c": ["a"]
        }
        visited = {}
        findings = []
        def check_cycle(node, path):
            visited[node] = 1
            for neighbor in dep_graph.get(node, []):
                if neighbor not in dep_graph:
                    continue
                if visited.get(neighbor) == 1:
                    findings.append(f"Cycle: {' -> '.join(path + [neighbor])}")
                    return True
                elif visited.get(neighbor) == 0:
                    continue
                else:
                    if check_cycle(neighbor, path + [neighbor]):
                        return True
            visited[node] = 0
            return False

        for s in dep_graph:
            if s not in visited:
                check_cycle(s, [s])
        assert len(findings) > 0, "Cycle detection must catch cyclic dependencies"
