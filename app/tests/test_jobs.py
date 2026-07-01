from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200


def test_jobs():
    response = client.get("/jobs")
    assert response.status_code == 200


def test_dashboard():
    response = client.get("/dashboard")
    assert response.status_code == 200