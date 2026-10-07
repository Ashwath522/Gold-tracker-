import base64
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings


def _hdr(user, pwd):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pwd}".encode()).decode()}


@pytest.fixture
def secured(monkeypatch):
    monkeypatch.setattr(settings, "APP_USERNAME", "ash")
    monkeypatch.setattr(settings, "APP_PASSWORD", "s3cret")
    return TestClient(app)


def test_open_when_no_credentials_configured():
    assert TestClient(app).get("/api/model/explanation").status_code == 200


def test_requires_auth_when_configured(secured):
    r = secured.get("/api/model/explanation")
    assert r.status_code == 401
    assert "Basic" in r.headers["www-authenticate"]
    assert secured.get("/api/model/explanation", headers=_hdr("ash", "wrong")).status_code == 401
    assert secured.get("/api/model/explanation", headers=_hdr("ash", "s3cret")).status_code == 200


def test_health_stays_public(secured):
    assert secured.get("/api/health").status_code == 200
