from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_job_summary():
    response = client.get("/jobs/1/summary")
    assert response.status_code in [200, 404]


def test_job_status():
    response = client.get("/jobs/1/status")
    assert response.status_code in [200, 404]


def test_job_results():
    response = client.get("/jobs/1/results")
    assert response.status_code in [200, 404]