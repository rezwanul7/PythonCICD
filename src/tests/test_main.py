import socket
from pathlib import Path
from re import fullmatch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_get_root_uses_default_environment_without_writing_upload_file(
    client, monkeypatch
):
    demo_file = Path("uploads/demo.txt")
    original_content = demo_file.read_text()
    monkeypatch.delenv("APP_ENV", raising=False)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "hello world!",
        "name": "PythonCICD",
        "version": "0.1.0",
        "environment": "UNKNOWN",
        "served_by": socket.gethostname(),
    }
    assert "sys_user" not in response.json()
    assert demo_file.read_text() == original_content


def test_get_root_uses_configured_environment(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["environment"] == "test"


def test_startup_probe(client):
    response = client.get("/health/startup")

    assert response.status_code == 200
    assert response.json() == {
        "status": "started",
        "served_by": socket.gethostname(),
    }


def test_liveness_probe(client):
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "alive",
        "served_by": socket.gethostname(),
    }


def test_readiness_probe(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "served_by": socket.gethostname(),
    }


def test_readiness_probe_returns_503_when_app_is_not_ready(client):
    app.state.ready = False

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Application is not ready",
        "served_by": socket.gethostname(),
    }


def test_legacy_health_endpoint_is_removed(client):
    response = client.get("/health")

    assert response.status_code == 404
    assert response.json()["served_by"] == socket.gethostname()


def test_get_item_without_query(client):
    response = client.get("/items/42")

    assert response.status_code == 200
    assert response.json() == {
        "item_id": 42,
        "q": None,
        "served_by": socket.gethostname(),
    }


def test_get_item_with_query(client):
    response = client.get("/items/42", params={"q": "example"})

    assert response.status_code == 200
    assert response.json() == {
        "item_id": 42,
        "q": "example",
        "served_by": socket.gethostname(),
    }


def test_get_item_rejects_non_integer_id(client):
    response = client.get("/items/not-an-integer")

    assert response.status_code == 422
    assert response.json()["served_by"] == socket.gethostname()


def test_uploaded_demo_file_is_served(client):
    response = client.get("/uploads/demo.txt")

    assert response.status_code == 200
    assert response.content == Path("uploads/demo.txt").read_bytes()


def test_demo_file_is_not_served_as_a_public_asset(client):
    response = client.get("/public/demo.txt")

    assert response.status_code == 404


def test_test_rw_router_reads_and_writes_upload_file(client):
    demo_file = Path("uploads/demo.txt")
    original_bytes = demo_file.read_bytes()
    original_content = demo_file.read_text(encoding="utf-8").splitlines()
    updated_content = [
        "Updated through the test-rw router.",
        "Appended through the test-rw router.",
    ]

    try:
        read_response = client.get("/test-rw/uploads")
        write_response = client.put(
            "/test-rw/uploads", json={"content": updated_content}
        )

        assert read_response.status_code == 200
        assert read_response.json() == {
            "content": original_content,
            "served_by": socket.gethostname(),
        }
        assert write_response.status_code == 200
        assert write_response.json() == {
            "content": [*original_content, *updated_content],
            "served_by": socket.gethostname(),
        }
        assert demo_file.read_text(encoding="utf-8").splitlines() == [
            *original_content,
            *updated_content,
        ]
    finally:
        demo_file.write_bytes(original_bytes)


def test_test_rw_router_writes_hostname_and_timestamp_without_content(client):
    demo_file = Path("uploads/demo.txt")
    original_bytes = demo_file.read_bytes()

    try:
        response = client.put("/test-rw/uploads", json={})

        assert response.status_code == 200
        pattern = (
            rf"{socket.gethostname()} - "
            r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}"
        )
        appended_content = response.json()["content"][-1]
        assert fullmatch(pattern, appended_content)
        assert (
            demo_file.read_text(encoding="utf-8").splitlines()
            == response.json()["content"]
        )
    finally:
        demo_file.write_bytes(original_bytes)


def test_info_endpoint_is_removed(client):
    response = client.get("/info")

    assert response.status_code == 404
