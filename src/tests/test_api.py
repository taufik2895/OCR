from fastapi.testclient import TestClient


def test_health_and_dashboard(client: TestClient) -> None:
    assert client.get("/api/v1/health").json() == {"status": "healthy"}
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_upload_and_retrieve_document(client: TestClient) -> None:
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("scan.png", b"not-empty", "image/png")},
    )
    assert upload.status_code == 201
    payload = upload.json()
    result = client.get(f"/api/v1/documents/{payload['id']}")
    assert result.status_code == 200
    assert result.json()["status"] == "uploaded"


def test_rejects_unsupported_upload(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("malware.exe", b"content", "application/octet-stream")},
    )
    assert response.status_code == 422
