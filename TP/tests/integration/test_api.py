import struct
import json
from unittest.mock import patch, MagicMock
import pytest
from triangulator.models.serialize import PointSetSerializer, TrianglesSerializer, PointSet
from triangulator.triangulation import app

@pytest.fixture(scope="session")
def server():
    return app.test_client()


def test_api_triangulate_success(server):
    """Test triangulation endpoint with valid PointSet."""
    points = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    pointset = PointSet(points)
    binary_ps = PointSetSerializer.serialize(pointset)

    # Mock fetch_point_set to return binary PointSet
    with patch("triangulator.triangulation.fetch_point_set", return_value=binary_ps):
        response = server.get("/triangulate/test123")
        
        assert response.status_code == 200
        triangles = TrianglesSerializer.deserialize(response.data)
        assert len(triangles.vertices) == 3
        assert len(triangles.triangles) >= 1


def test_api_triangulate_invalid_id(server):
    """Test triangulation with invalid point set ID."""
    # Mock fetch_point_set to return None (not found)
    with patch("triangulator.triangulation.fetch_point_set", return_value=None):
        response = server.get("/triangulate/invalid")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert "not found" in data["error"].lower()


def test_api_triangulate_insufficient_points(server):
    """Test triangulation with fewer than 3 points."""
    pointset = PointSet([(0.0, 0.0), (1.0, 1.0)])
    binary_ps = PointSetSerializer.serialize(pointset)
    
    with patch("triangulator.triangulation.fetch_point_set", return_value=binary_ps):
        response = server.get("/triangulate/test_insufficient")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


def test_api_triangulate_collinear_points(server):
    """Test triangulation with collinear points."""
    pointset = PointSet([(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)])
    binary_ps = PointSetSerializer.serialize(pointset)
    
    with patch("triangulator.triangulation.fetch_point_set", return_value=binary_ps):
        response = server.get("/triangulate/test_collinear")
        # Collinear points can still form a degenerate triangle
        assert response.status_code in [200, 400]


def test_api_triangulate_malformed_binary(server):
    """Test triangulation with malformed binary data."""
    # Mock with invalid/truncated binary
    with patch("triangulator.triangulation.fetch_point_set", return_value=b"\x01\x00"):
        response = server.get("/triangulate/malformed")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data