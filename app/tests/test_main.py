from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_info():
    response = client.get("/info")
    assert response.status_code == 200
    assert response.json() == {"name": "ob-sample-fast-api", "version": "1.0.0"}
