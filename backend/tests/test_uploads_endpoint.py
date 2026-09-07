import pytest
from starlette.testclient import TestClient
from app.main import app

def test_uploads_flow():
    client = TestClient(app)

    # 1. Request presigned upload URL
    res = client.post(
        "/api/v1/uploads",
        json={"filename": "test-photo.png", "content_type": "image/png"}
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "upload_url" in data
    assert "public_url" in data
    assert "object_key" in data

    upload_url = data["upload_url"]
    public_url = data["public_url"]
    object_key = data["object_key"]

    # 2. Upload binary payload via PUT
    fake_png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    # If upload_url is absolute or path:
    if "/api/v1/uploads/storage/" in upload_url:
        path = upload_url[upload_url.index("/api/v1/uploads/storage/"):]
        put_res = client.put(path, content=fake_png_bytes, headers={"Content-Type": "image/png"})
        assert put_res.status_code == 200, put_res.text
        put_data = put_res.json()
        assert put_data["status"] == "success"
        assert put_data["bytes_received"] == len(fake_png_bytes)

        # 3. Retrieve binary payload via GET file
        get_path = public_url[public_url.index("/api/v1/uploads/file/"):]
        get_res = client.get(get_path)
        assert get_res.status_code == 200
        assert get_res.content == fake_png_bytes
        assert get_res.headers["content-type"] == "image/png"
