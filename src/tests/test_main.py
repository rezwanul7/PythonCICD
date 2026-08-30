import socket
from pathlib import Path
from re import fullmatch

import pytest
from fastapi.testclient import TestClient

from src.main import app

PUBLIC_DEMO_FILE = Path("public/demo.txt")
UPLOADED_FILE = Path("uploads/uploaded.txt")


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def missing_uploaded_file():
    original_bytes = UPLOADED_FILE.read_bytes() if UPLOADED_FILE.exists() else None
    UPLOADED_FILE.unlink(missing_ok=True)
    try:
        yield
    finally:
        if original_bytes is None:
            UPLOADED_FILE.unlink(missing_ok=True)
        else:
            UPLOADED_FILE.write_bytes(original_bytes)


def test_get_root_uses_default_environment_without_writing_upload_file(
    client, monkeypatch, missing_uploaded_file
):
    monkeypatch.delenv("APP_ENV", raising=False)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "hello world!",
        "name": "FastShip",
        "version": "0.2.0",
        "environment": "UNKNOWN",
        "served_by": socket.gethostname(),
    }
    assert "sys_user" not in response.json()
    assert not UPLOADED_FILE.exists()


def test_get_root_uses_configured_environment(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["environment"] == "test"


def test_openapi_metadata_uses_fastship_name_and_version(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"] == {
        "title": "FastShip",
        "version": "0.2.0",
    }


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


def test_public_demo_file_is_served_as_an_immutable_asset(client):
    response = client.get("/public/demo.txt")

    assert response.status_code == 200
    assert response.content == PUBLIC_DEMO_FILE.read_bytes()


def test_missing_upload_returns_not_found(client, missing_uploaded_file):
    api_response = client.get("/test-rw/uploads")
    write_response = client.put(
        "/test-rw/uploads", json={"content": ["Cannot write before upload."]}
    )
    static_response = client.get("/uploads/uploaded.txt")
    legacy_response = client.get("/uploads/demo.txt")

    assert api_response.status_code == 404
    assert api_response.json() == {
        "detail": "Uploaded file does not exist",
        "served_by": socket.gethostname(),
    }
    assert write_response.status_code == 404
    assert write_response.json() == api_response.json()
    assert not UPLOADED_FILE.exists()
    assert static_response.status_code == 404
    assert legacy_response.status_code == 404


def test_test_rw_router_uploads_and_appends_to_upload_file(
    client, missing_uploaded_file
):
    public_bytes = PUBLIC_DEMO_FILE.read_bytes()
    initial_content = ["Uploaded through the test-rw router."]
    appended_content = ["Appended through the test-rw router."]

    upload_response = client.post("/test-rw/uploads", json={"content": initial_content})
    append_response = client.put("/test-rw/uploads", json={"content": appended_content})
    static_response = client.get("/uploads/uploaded.txt")

    assert upload_response.status_code == 200
    assert upload_response.json() == {
        "content": initial_content,
        "served_by": socket.gethostname(),
    }
    assert append_response.status_code == 200
    assert append_response.json() == {
        "content": [*initial_content, *appended_content],
        "served_by": socket.gethostname(),
    }
    assert UPLOADED_FILE.read_text(encoding="utf-8").splitlines() == [
        *initial_content,
        *appended_content,
    ]
    assert static_response.status_code == 200
    assert static_response.content == UPLOADED_FILE.read_bytes()
    assert PUBLIC_DEMO_FILE.read_bytes() == public_bytes


def test_upload_with_empty_content_creates_an_empty_file(client, missing_uploaded_file):
    response = client.post("/test-rw/uploads", json={"content": []})
    read_response = client.get("/test-rw/uploads")
    static_response = client.get("/uploads/uploaded.txt")

    expected = {"content": [], "served_by": socket.gethostname()}
    assert response.status_code == 200
    assert response.json() == expected
    assert read_response.status_code == 200
    assert read_response.json() == expected
    assert static_response.status_code == 200
    assert static_response.content == b""
    assert UPLOADED_FILE.exists()
    assert UPLOADED_FILE.stat().st_size == 0


@pytest.mark.parametrize(
    "request_kwargs",
    [{}, {"json": None}, {"json": {"content": None}}],
)
def test_test_rw_router_uploads_default_content_without_content(
    client, missing_uploaded_file, request_kwargs
):
    response = client.post("/test-rw/uploads", **request_kwargs)

    assert response.status_code == 200
    pattern = (
        rf"{socket.gethostname()} - "
        r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}"
    )
    appended_content = response.json()["content"][-1]
    assert fullmatch(pattern, appended_content)
    assert (
        UPLOADED_FILE.read_text(encoding="utf-8").splitlines()
        == response.json()["content"]
    )


def test_upload_replaces_existing_content(client, missing_uploaded_file):
    initial_content = ["First upload.", "This line will be replaced."]
    replacement_content = ["Replacement upload."]

    client.post("/test-rw/uploads", json={"content": initial_content})
    response = client.post("/test-rw/uploads", json={"content": replacement_content})

    assert response.status_code == 200
    assert response.json() == {
        "content": replacement_content,
        "served_by": socket.gethostname(),
    }
    assert UPLOADED_FILE.read_text(encoding="utf-8").splitlines() == replacement_content


def test_empty_write_leaves_existing_upload_unchanged(client, missing_uploaded_file):
    initial_content = ["Existing upload."]
    client.post("/test-rw/uploads", json={"content": initial_content})
    original_bytes = UPLOADED_FILE.read_bytes()

    response = client.put("/test-rw/uploads", json={"content": []})

    assert response.status_code == 200
    assert response.json() == {
        "content": initial_content,
        "served_by": socket.gethostname(),
    }
    assert UPLOADED_FILE.read_bytes() == original_bytes


def test_info_endpoint_is_removed(client):
    response = client.get("/info")

    assert response.status_code == 404
