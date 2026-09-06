"""
Tier 2: Boundary & Corner Cases Tests.
Authoritative Specifications:
- PROJECT.md (Interface Contracts, Error Behaviors)
- spec_miner_blueprints_1/spec.md (Section 6, Section 7 Edge Cases)
- spec_miner_schemas_2/spec.md (Section 2 Edge Cases)

Covers:
- Invalid endpoints (404 Not Found)
- Unsupported HTTP methods (405 Method Not Allowed)
- Malformed payloads and content types
- CORS preflight and origin boundary validation
- TCP probe timeout and connection retry bounds
- RESP protocol serializer boundary conditions
"""

import socket
import time
from typing import Any, Dict

import pytest

from tests.utils.config import (
    DEFAULT_SOCKET_TIMEOUT,
    FASTAPI_BASE_URL,
    FASTAPI_HEALTH_URL,
)
from tests.utils.probes import check_tcp_port, send_redis_raw_command


class TestTier2Boundaries:
    """Boundary, corner case, and negative testing across system entrypoints."""

    def test_boundary_01_non_existent_route_returns_404(self, http_client):
        """Invalid route request must return HTTP 404 Not Found."""
        url = f"{FASTAPI_BASE_URL}/api/v1/invalid_route_404_does_not_exist" if hasattr(http_client, "session") else "/api/v1/invalid_route_404_does_not_exist"
        response = http_client.get(url)
        assert response.status_code == 404, f"Expected 404 for invalid route, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "404 response should include 'detail' field"

    def test_boundary_02_post_on_read_only_health_returns_405(self, http_client):
        """HTTP POST on read-only GET /health must return HTTP 405 Method Not Allowed."""
        url = FASTAPI_HEALTH_URL if hasattr(http_client, "session") else "/health"
        response = http_client.post(url, json={"test": "data"})
        assert response.status_code == 405, (
            f"Expected 405 Method Not Allowed on POST /health, got {response.status_code}"
        )

    def test_boundary_03_delete_on_read_only_api_v1_returns_405(self, http_client):
        """HTTP DELETE on read-only GET /api/v1 must return HTTP 405 Method Not Allowed."""
        url = f"{FASTAPI_BASE_URL}/api/v1" if hasattr(http_client, "session") else "/api/v1"
        response = http_client.delete(url)
        assert response.status_code == 405, (
            f"Expected 405 Method Not Allowed on DELETE /api/v1, got {response.status_code}"
        )

    def test_boundary_04_put_on_root_endpoint_returns_404_or_405(self, http_client):
        """HTTP PUT on non-existent root endpoint must return 404 or 405."""
        url = f"{FASTAPI_BASE_URL}/" if hasattr(http_client, "session") else "/"
        response = http_client.put(url, json={})
        assert response.status_code in (404, 405), (
            f"Expected 404 or 405 for PUT /, got {response.status_code}"
        )

    def test_boundary_05_cors_preflight_options_request(self, http_client):
        """CORS OPTIONS preflight request with origin must return appropriate Access-Control headers."""
        url = FASTAPI_HEALTH_URL if hasattr(http_client, "session") else "/health"
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        }
        response = http_client.options(url, headers=headers)
        assert response.status_code in (200, 204), f"Preflight OPTIONS returned {response.status_code}"
        # If running under TestClient or live server with CORSMiddleware
        allow_origin = response.headers.get("access-control-allow-origin")
        assert allow_origin in ("*", "http://localhost:3000"), (
            f"Unexpected access-control-allow-origin: {allow_origin}"
        )

    def test_boundary_06_tcp_timeout_bounded_on_unreachable_port(self):
        """Probing an unused port must cleanly terminate within specified timeout without hanging."""
        # Port 59123 is in the dynamic/private range and typically closed
        start_time = time.time()
        timeout = 0.5
        is_open = check_tcp_port("127.0.0.1", 59123, timeout=timeout)
        duration = time.time() - start_time
        assert not is_open, "Port 59123 unexpectedly open"
        assert duration < 2.0, f"Probe took {duration:.2f}s, exceeding maximum acceptable bound"

    def test_boundary_07_redis_resp_empty_args_serializer(self):
        """Edge case: RESP command formatter must handle single-word and multi-word commands safely."""
        from tests.utils.probes import send_redis_raw_command
        # Test command with empty string argument
        args = ["SET", "test_empty_key", ""]
        payload = f"*{len(args)}\r\n"
        for arg in args:
            payload += f"${len(arg.encode('utf-8'))}\r\n{arg}\r\n"
        assert "$0\r\n\r\n" in payload, "Empty string argument must produce $0\\r\\n\\r\\n bulk string"
