import struct
import pytest
from models.serialize import PointSetSerializer, TrianglesSerializer

@pytest.fixture
def client():
    from app import app  # your Flask app
    return app.test_client()


def test_api_pointset_serialize(client):
    # Binary for 2 points
    data = struct.pack("<I", 2)
    data += struct.pack("<ff", 0.0, 0.0)
    data += struct.pack("<ff", 1.0, 1.0)

    r = client.post("/pointset/deserialize", data=data)
    assert r.status_code == 200
    assert b"points" in r.data  # JSON response


def test_api_triangles_serialize(client):
    # minimal triangle
    data = struct.pack("<I", 3)
    data += struct.pack("<ff", 0, 0)
    data += struct.pack("<ff", 1, 0)
    data += struct.pack("<ff", 0, 1)

    data += struct.pack("<I", 1)
    data += struct.pack("<III", 0, 1, 2)

    r = client.post("/triangles/deserialize", data=data)
    assert r.status_code == 200
    assert b"triangles" in r.data
