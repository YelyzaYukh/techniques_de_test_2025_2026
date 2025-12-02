import pytest
import struct
import requests
from unittest.mock import patch
from models.serialize import PointSet, PointSetSerializer


def test_pointset_client_upload_success():
    pointset = PointSet([(0.0, 0.0), (1.0, 1.0)])
    payload = PointSetSerializer.serialize(pointset)

    # Fake server binary response
    response_data = struct.pack("<I", 1) + struct.pack("<ff", 0.0, 0.0)

    class FakeResponse:
        status_code = 200
        content = response_data

    with patch("requests.post", return_value=FakeResponse()):
        r = requests.post("http://incorrect/api/upload", data=payload)

        assert r.status_code == 200
        restored = PointSetSerializer.deserialize(r.content)
        assert len(restored.points) == 1
        assert restored.points[0] == (0.0, 0.0)


def test_pointset_client_upload_failure():
    pointset = PointSet([(0.0, 0.0)])
    payload = PointSetSerializer.serialize(pointset)

    class FakeError:
        status_code = 400
        content = b""

    with patch("requests.post", return_value=FakeError()):
        r = requests.post("http://incorrect/api/upload", data=payload)
        assert r.status_code == 400
