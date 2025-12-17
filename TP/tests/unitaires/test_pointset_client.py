import pytest
import struct
from unittest.mock import patch, Mock
from triangulator.models.serialize import PointSet, PointSetSerializer

def test_pointset_creation():
    """Test PointSet object creation."""
    points = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.5)]
    ps = PointSet(points)

    assert ps.points == points
    assert len(ps.points) == 3


def test_pointset_empty():
    """Test PointSet with no points."""
    ps = PointSet([])

    assert ps.points == []
    assert len(ps.points) == 0


def test_pointset_serialization():
    """Test PointSet serialization to binary."""
    ps = PointSet([(0.0, 0.0), (1.0, 1.0)])
    data = PointSetSerializer.serialize(ps)

    # Check format: <I count> <ff x1 y1> <ff x2 y2>
    assert len(data) == 4 + 2 * 8
    count = struct.unpack("<I", data[:4])[0]
    assert count == 2


def test_pointset_deserialization():
    """Test PointSet deserialization from binary."""
    data = struct.pack("<I", 2)
    data += struct.pack("<ff", 0.0, 0.0)
    data += struct.pack("<ff", 1.0, 1.0)

    ps = PointSetSerializer.deserialize(data)

    assert len(ps.points) == 2
    assert ps.points[0][0] == pytest.approx(0.0)
    assert ps.points[1][1] == pytest.approx(1.0)


def test_pointset_roundtrip():
    """Test PointSet serialize/deserialize roundtrip."""
    original = PointSet([(1.5, 2.5), (-1.0, 3.0), (0.0, 0.0)])

    binary = PointSetSerializer.serialize(original)
    restored = PointSetSerializer.deserialize(binary)

    assert len(restored.points) == len(original.points)
    for (ox, oy), (rx, ry) in zip(original.points, restored.points):
        assert rx == pytest.approx(ox)
        assert ry == pytest.approx(oy)
