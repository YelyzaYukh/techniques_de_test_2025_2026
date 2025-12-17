"""Tests unitaires pour la sérialisation/désérialisation binaire des PointSet.

Auteur: Yelyzaveta YUKHNOVA

Ce module teste les conversions entre structures Python et format binaire
pour PointSet et Triangles selon la spécification OpenAPI.
"""

import struct
import sys
import math
import pytest

from triangulator.models.serialize import (
    PointSet,
    Triangles,
    PointSetSerializer,
    TrianglesSerializer,
)


FLOAT32_MAX = 3.4028234663852886e+38


# helper for tolerant float comparisons
def _assert_points_close(list_a, list_b):
    assert len(list_a) == len(list_b)
    for (ax, ay), (bx, by) in zip(list_a, list_b):
        assert ax == pytest.approx(bx)
        assert ay == pytest.approx(by)


# ============================================================================ #
#  BASIC SERIALIZATION TESTS
# ============================================================================ #

class TestPointSetSerialization:

    def test_serialize_simple_pointset(self):
        points = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
        ps = PointSet(points)

        data = PointSetSerializer.serialize(ps)

        assert struct.unpack("<I", data[:4])[0] == 3
        assert len(data) == 4 + 3 * 8

        x1, y1 = struct.unpack('<ff', data[4:12])
        assert x1 == pytest.approx(0.0)
        assert y1 == pytest.approx(0.0)

        x2, y2 = struct.unpack('<ff', data[12:20])
        assert x2 == pytest.approx(1.0)
        assert y2 == pytest.approx(0.0)

        x3, y3 = struct.unpack('<ff', data[20:28])
        assert x3 == pytest.approx(0.0)
        assert y3 == pytest.approx(1.0)

    def test_deserialize_simple_pointset(self):
        data = struct.pack("<I", 3)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 0.0)
        data += struct.pack("<ff", 0.0, 1.0)

        ps = PointSetSerializer.deserialize(data)

        _assert_points_close(ps.points, [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)])

    def test_roundtrip_pointset(self):
        original = PointSet([(1.5, 2.5), (-1.0, 3.0), (0.0, 0.0)])

        data = PointSetSerializer.serialize(original)
        restored = PointSetSerializer.deserialize(data)

        # compare elementwise with tolerance (float32 quantization)
        _assert_points_close(restored.points, original.points)

    @pytest.mark.parametrize("points", [
        [(0.0, 0.0)],
        [(0.0, 0.0), (1.0, 1.0)],
        [(i * 0.1, i * 0.2) for i in range(10)],
        [(i * 1.0, i * 1.0) for i in range(100)],
    ])
    def test_various_sizes(self, points):
        ps = PointSet(points)
        data = PointSetSerializer.serialize(ps)

        expected_size = 4 + len(points) * 8
        assert len(data) == expected_size

        restored = PointSetSerializer.deserialize(data)
        _assert_points_close(restored.points, points)


# ============================================================================ #
#  EDGE CASES
# ============================================================================ #

class TestPointSetEdgeCases:

    def test_empty_pointset(self):
        ps = PointSet([])

        data = PointSetSerializer.serialize(ps)
        assert len(data) == 4
        assert struct.unpack("<I", data)[0] == 0

        restored = PointSetSerializer.deserialize(data)
        assert restored.points == []

    def test_negative_coordinates(self):
        ps = PointSet([(-5.5, -10.2), (-0.1, -100.0)])

        data = PointSetSerializer.serialize(ps)
        restored = PointSetSerializer.deserialize(data)

        assert restored.points[0][0] == pytest.approx(-5.5)
        assert restored.points[0][1] == pytest.approx(-10.2)

    def test_extreme_float_values(self):
        points = [
            (sys.float_info.max, sys.float_info.min),
            (-sys.float_info.max, 0.0),
        ]

        ps = PointSet(points)
        data = PointSetSerializer.serialize(ps)
        restored = PointSetSerializer.deserialize(data)

        assert len(restored.points) == 2

    def test_very_close_points(self):
        points = [(0.0, 0.0), (1e-7, 1e-7), (2e-7, 0.0)]

        ps = PointSet(points)
        data = PointSetSerializer.serialize(ps)
        restored = PointSetSerializer.deserialize(data)

        # float32 quantization: use tolerant comparison only
        _assert_points_close(restored.points, points)


# ============================================================================ #
#  ERROR CASES
# ============================================================================ #

class TestPointSetErrorCases:

    def test_deserialize_truncated_data(self):
        data = struct.pack("<I", 3)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 1.0)

        with pytest.raises(ValueError):
            PointSetSerializer.deserialize(data)

    def test_deserialize_too_short(self):
        with pytest.raises(ValueError):
            PointSetSerializer.deserialize(b"\x01\x00")

    def test_deserialize_empty_bytes(self):
        with pytest.raises(ValueError):
            PointSetSerializer.deserialize(b"")

    def test_deserialize_inconsistent_size(self):
        data = struct.pack("<I", 2)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 1.0)
        data += b"\x00\x00\x00\x00"  # garbage padding

        with pytest.raises(ValueError):
            PointSetSerializer.deserialize(data)

    def test_extra_bytes(self):
        data = struct.pack("<I", 1)
        data += struct.pack("<ff", 1.0, 2.0)
        data += b"\xFF\xFF\xFF\xFF"

        with pytest.raises(ValueError):
            PointSetSerializer.deserialize(data)


# ============================================================================ #
#  TRIANGLES SERIALIZATION TESTS
# ============================================================================ #

class TestTrianglesSerialization:

    def test_serialize_simple_triangles(self):
        vertices = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
        triangles = [(0, 1, 2)]
        obj = Triangles(vertices, triangles)

        data = TrianglesSerializer.serialize(obj)

        # check vertex count
        assert struct.unpack("<I", data[:4])[0] == 3
        # triangle count is after vertices: 4 + (3 * 8) = 28
        assert struct.unpack("<I", data[28:32])[0] == 1
        assert len(data) == 4 + 3 * 8 + 4 + 1 * 12

        # check vertex data
        x1, y1 = struct.unpack('<ff', data[4:12])
        assert x1 == pytest.approx(0.0)
        assert y1 == pytest.approx(0.0)

        x2, y2 = struct.unpack('<ff', data[12:20])
        assert x2 == pytest.approx(1.0)
        assert y2 == pytest.approx(0.0)

        x3, y3 = struct.unpack('<ff', data[20:28])
        assert x3 == pytest.approx(0.0)
        assert y3 == pytest.approx(1.0)

        # check triangle data (starts at 32)
        a, b, c = struct.unpack('<III', data[32:44])
        assert a == 0
        assert b == 1
        assert c == 2

    def test_deserialize_simple_triangles(self):
        data = struct.pack("<I", 3)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 0.0)
        data += struct.pack("<ff", 0.0, 1.0)
        data += struct.pack("<I", 1)
        data += struct.pack("<III", 0, 1, 2)

        obj = TrianglesSerializer.deserialize(data)

        _assert_points_close(obj.vertices, [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)])
        assert obj.triangles == [(0, 1, 2)]

    def test_roundtrip_triangles(self):
        original = Triangles(
            vertices=[(1.5, 2.5), (-1.0, 3.0), (0.0, 0.0)],
            triangles=[(0, 1, 2)],
        )

        data = TrianglesSerializer.serialize(original)
        restored = TrianglesSerializer.deserialize(data)

        # compare vertices elementwise with tolerance (float32 quantization)
        _assert_points_close(restored.vertices, original.vertices)
        # compare triangle indices (exact match)
        assert restored.triangles == original.triangles

    @pytest.mark.parametrize("vertices,triangles", [
        ([(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)], []),
        ([(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)], [(0, 1, 2)]),
        ([(i * 0.1, i * 0.2) for i in range(10)], [(0, 1, 2)]),
        ([(i * 1.0, i * 1.0) for i in range(100)], [(0, 1, 2), (2, 3, 4)]),
    ])
    def test_various_sizes_triangles(self, vertices, triangles):
        obj = Triangles(vertices, triangles)
        data = TrianglesSerializer.serialize(obj)

        expected_size = 4 + len(vertices) * 8 + 4 + len(triangles) * 12
        assert len(data) == expected_size

        restored = TrianglesSerializer.deserialize(data)
        _assert_points_close(restored.vertices, vertices)
        assert restored.triangles == triangles


# ============================================================================ #
#  EDGE CASES FOR TRIANGLES
# ============================================================================ #

class TestTrianglesEdgeCases:

    def test_empty_triangles(self):
        obj = Triangles([], [])

        data = TrianglesSerializer.serialize(obj)
        assert len(data) == 8
        assert struct.unpack("<I", data[:4])[0] == 0
        assert struct.unpack("<I", data[4:8])[0] == 0

        restored = TrianglesSerializer.deserialize(data)
        assert restored.vertices == []
        assert restored.triangles == []

    def test_negative_coordinates_triangles(self):
        # Need 3 vertices to form a valid triangle with indices (0, 1, 2)
        obj = Triangles([(-5.5, -10.2), (-0.1, -100.0), (1.0, 2.0)], [(0, 1, 2)])

        data = TrianglesSerializer.serialize(obj)
        restored = TrianglesSerializer.deserialize(data)

        assert restored.vertices[0][0] == pytest.approx(-5.5)
        assert restored.vertices[0][1] == pytest.approx(-10.2)

    def test_extreme_float_values_triangles(self):
        vertices = [
            (sys.float_info.max, sys.float_info.min),
            (-sys.float_info.max, 0.0),
            (0.0, 0.0),
        ]
        obj = Triangles(vertices, [])

        data = TrianglesSerializer.serialize(obj)
        restored = TrianglesSerializer.deserialize(data)

        assert len(restored.vertices) == 3
        assert restored.triangles == []

    def test_very_close_vertices_triangles(self):
        vertices = [(0.0, 0.0), (1e-7, 1e-7), (2e-7, 0.0)]
        obj = Triangles(vertices, [(0, 1, 2)])

        data = TrianglesSerializer.serialize(obj)
        restored = TrianglesSerializer.deserialize(data)

        # float32 quantization: use tolerant comparison only
        _assert_points_close(restored.vertices, vertices)

    def test_serialize_triangles_with_large_indices(self):
        vertices = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
        triangles = [(0, 1, 2), (2, 1, 0), (1, 0, 2)]
        obj = Triangles(vertices, triangles)

        data = TrianglesSerializer.serialize(obj)

        # check vertex and triangle counts
        assert struct.unpack("<I", data[:4])[0] == 3
        # triangle count is after vertices: 4 + (3 * 8) = 28
        assert struct.unpack("<I", data[28:32])[0] == 3
        assert len(data) == 4 + 3 * 8 + 4 + 3 * 12

        # check triangle data (starts at 32)
        a, b, c = struct.unpack('<III', data[32:44])
        assert a == 0
        assert b == 1
        assert c == 2


# ============================================================================ #
#  ERROR CASES FOR TRIANGLES
# ============================================================================ #

class TestTrianglesErrorCases:

    def test_deserialize_truncated_data_triangles(self):
        data = struct.pack("<I", 3)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 0.0)
        data += struct.pack("<ff", 0.0, 1.0)
        data += struct.pack("<I", 1)
        data += struct.pack("<III", 0, 1, 2)

        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(data[:-4])

    def test_deserialize_too_short_triangles(self):
        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(b"\x01\x00")

    def test_deserialize_empty_bytes_triangles(self):
        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(b"")

    def test_deserialize_inconsistent_size_triangles(self):
        data = struct.pack("<I", 2)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 1.0)
        data += struct.pack("<I", 1)
        data += struct.pack("<III", 0, 1, 2)
        data += b"\x00\x00\x00\x00"  # garbage padding

        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(data)

    def test_extra_bytes_triangles(self):
        data = struct.pack("<I", 1)
        data += struct.pack("<ff", 1.0, 2.0)
        data += struct.pack("<I", 1)
        data += struct.pack("<III", 0, 1, 2)
        data += b"\xFF\xFF\xFF\xFF"

        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(data)