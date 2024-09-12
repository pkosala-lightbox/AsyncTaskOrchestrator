
import pytest
from fastapi.testclient import TestClient
from fastapi_app.app import app

client = TestClient(app)

def test_process_event():
    response = client.post("/process_event", json={"data": "test data"})
    assert response.status_code == 200
    assert "request_id" in response.json()

def test_status():
    response = client.get("/status/1")
    assert response.status_code == 200
    assert response.json()["status"] in ["queued", "completed", "pending"]

def test_result():
    response = client.get("/result/1")
    assert response.status_code == 200
    assert "result" in response.json() or "error" in response.json()
