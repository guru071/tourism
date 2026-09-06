"""
Network probes, protocol helpers, and manifest inspectors for E2E testing.
Works with both live networked services and filesystem artifacts.
"""

import json
import os
import socket
import struct
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

from tests.utils.config import (
    ALEMBIC_DIR,
    ALEMBIC_INI_FILE,
    BACKEND_DIR,
    DEFAULT_HTTP_TIMEOUT,
    DEFAULT_SOCKET_TIMEOUT,
    DOCKER_COMPOSE_FILE,
    FRONTEND_DIR,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
    PROJECT_ROOT,
    REDIS_HOST,
    REDIS_PORT,
)


def check_tcp_port(host: str, port: int, timeout: float = DEFAULT_SOCKET_TIMEOUT) -> bool:
    """Check whether a TCP port is open and listening."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        res = s.connect_ex((host, port))
        return res == 0
    except Exception:
        return False
    finally:
        s.close()


def send_redis_raw_command(
    host: str,
    port: int,
    *args: str,
    timeout: float = DEFAULT_SOCKET_TIMEOUT
) -> Tuple[bool, str]:
    """
    Send a RESP formatted command to Redis over raw TCP socket.
    Returns (success, response_string).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        # Format as RESP array: *<num_args>\r\n$<len>\r\n<arg>\r\n...
        payload = f"*{len(args)}\r\n"
        for arg in args:
            payload += f"${len(arg.encode('utf-8'))}\r\n{arg}\r\n"
        s.sendall(payload.encode("utf-8"))
        response = s.recv(4096).decode("utf-8", errors="replace")
        return True, response
    except Exception as exc:
        return False, str(exc)
    finally:
        s.close()


def probe_postgres_wire_protocol(
    host: str,
    port: int,
    timeout: float = DEFAULT_SOCKET_TIMEOUT
) -> Tuple[bool, str]:
    """
    Probe PostgreSQL server by sending a standard SSLRequest packet.
    PostgreSQL responds with a single byte: 'S' (SSL supported) or 'N' (SSL denied).
    Returns (success, description).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        # Postgres SSLRequest code: 80877103 (1234.5679)
        # Packet length = 8 bytes (4 bytes length + 4 bytes code)
        packet = struct.pack("!II", 8, 80877103)
        s.sendall(packet)
        resp = s.recv(1)
        if resp in (b"S", b"N"):
            return True, f"Valid PostgreSQL protocol handshake received: {resp.decode('ascii')}"
        return False, f"Unexpected response from port {port}: {resp!r}"
    except Exception as exc:
        return False, str(exc)
    finally:
        s.close()


def http_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[bytes] = None,
    json_payload: Optional[Any] = None,
    timeout: float = DEFAULT_HTTP_TIMEOUT
) -> Tuple[int, Dict[str, str], str]:
    """
    Perform HTTP request with status code, response headers, and body string.
    Gracefully handles connection failures.
    """
    req_headers = headers.copy() if headers else {}
    body_bytes = None

    if json_payload is not None:
        body_bytes = json.dumps(json_payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    elif data is not None:
        body_bytes = data

    req = urllib.request.Request(
        url,
        data=body_bytes,
        headers=req_headers,
        method=method.upper()
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            resp_headers = dict(response.getheaders())
            content = response.read().decode("utf-8", errors="replace")
            return status, resp_headers, content
    except urllib.error.HTTPError as http_err:
        content = http_err.read().decode("utf-8", errors="replace")
        return http_err.code, dict(http_err.headers), content
    except Exception as exc:
        return 0, {}, str(exc)


def load_docker_compose_manifest() -> Dict[str, Any]:
    """Load and parse docker-compose.yml."""
    if not DOCKER_COMPOSE_FILE.exists():
        raise FileNotFoundError(f"docker-compose.yml not found at {DOCKER_COMPOSE_FILE}")
    with open(DOCKER_COMPOSE_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def inspect_alembic_setup() -> Dict[str, Any]:
    """Inspect alembic configuration and script directory."""
    results = {
        "ini_exists": ALEMBIC_INI_FILE.exists(),
        "env_exists": (ALEMBIC_DIR / "env.py").exists(),
        "versions_dir_exists": (ALEMBIC_DIR / "versions").exists(),
        "ini_content": "",
        "env_content": "",
        "versions": []
    }
    if results["ini_exists"]:
        results["ini_content"] = ALEMBIC_INI_FILE.read_text(encoding="utf-8")
    if results["env_exists"]:
        results["env_content"] = (ALEMBIC_DIR / "env.py").read_text(encoding="utf-8")
    if results["versions_dir_exists"]:
        results["versions"] = [p.name for p in (ALEMBIC_DIR / "versions").glob("*.py")]
    return results
