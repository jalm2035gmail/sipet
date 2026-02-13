from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Sistema de Planificación Estratégica" in response.json()["message"]

def test_docs():
    response = client.get("/docs")
    assert response.status_code == 200
