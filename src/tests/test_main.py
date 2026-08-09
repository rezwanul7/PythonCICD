from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_get_root_uses_default_environment_without_writing_public_file(monkeypatch):
    demo_file = Path("public/demo.txt")
    original_content = demo_file.read_text()
    monkeypatch.delenv("APP_ENV", raising=False)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "hello world!",
        "name": "PythonCICD",
        "version": "0.1.0",
        "environment": "UNKNOWN",
    }
    assert "sys_user" not in response.json()
    assert demo_file.read_text() == original_content


def test_get_root_uses_configured_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["environment"] == "test"


def test_get_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_item_without_query():
    response = client.get("/items/42")

    assert response.status_code == 200
    assert response.json() == {"item_id": 42, "q": None}


def test_get_item_with_query():
    response = client.get("/items/42", params={"q": "example"})

    assert response.status_code == 200
    assert response.json() == {"item_id": 42, "q": "example"}


def test_get_item_rejects_non_integer_id():
    response = client.get("/items/not-an-integer")

    assert response.status_code == 422


def test_static_demo_file_is_served():
    response = client.get("/public/demo.txt")

    assert response.status_code == 200
    assert response.text == Path("public/demo.txt").read_text()


def test_info_endpoint_is_removed():
    response = client.get("/info")

    assert response.status_code == 404
