"""Shared fixtures."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MOCK_DIR = PROJECT_ROOT / "data" / "mock"


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def mock_dir() -> Path:
    return MOCK_DIR
