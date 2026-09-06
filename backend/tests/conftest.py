import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from starlette.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """TestClient fixture with app lifespan execution."""
    with TestClient(app) as test_client:
        yield test_client
