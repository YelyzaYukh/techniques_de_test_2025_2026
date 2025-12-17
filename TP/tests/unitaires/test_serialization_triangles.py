"""Tests unitaires pour la sérialisation/désérialisation binaire des Triangles.

Auteur: Yelyzaveta YUKHNOVA

Ce module teste les conversions entre structures Python et format binaire
pour Triangles selon la spécification OpenAPI.
"""

import struct
import sys
import pytest

from triangulator.models.serialize import (
    Triangles,
    TrianglesSerializer,
)


# helper for tolerant float comparisons
def _assert_points_close(list_a, list_b):
    assert len(list_a) == len(list_b)
    for (ax, ay), (bx, by) in zip(list_a, list_b):
        assert ax == pytest.approx(bx)
        assert ay == pytest.approx(by)


# ============================================================================ #
#  BASIC SERIALIZATION TESTS
# ============================================================================ #

class TestTrianglesBasicSerialization:

    def test_serialize_single_triangle(self):
        vertices = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
        triangles = [(0, 1, 2)]
        obj = Triangles(vertices, triangles)

        data = TrianglesSerializer.serialize(obj)

        assert struct.unpack("<I", data[:4])[0] == 3
        assert struct.unpack("<I", data[28:32])[0] == 1

    def test_deserialize_single_triangle(self):
        data = struct.pack("<I", 3)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 0.0)
        data += struct.pack("<ff", 0.0, 1.0)
        data += struct.pack("<I", 1)
        data += struct.pack("<III", 0, 1, 2)

        obj = TrianglesSerializer.deserialize(data)

        assert len(obj.vertices) == 3
        assert len(obj.triangles) == 1

    def test_roundtrip_single_triangle(self):
        original = Triangles(
            vertices=[(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)],
            triangles=[(0, 1, 2)],
        )

        data = TrianglesSerializer.serialize(original)
        restored = TrianglesSerializer.deserialize(data)

        _assert_points_close(restored.vertices, original.vertices)
        assert restored.triangles == original.triangles


# ============================================================================ #
#  EDGE CASES
# ============================================================================ #

class TestTrianglesEdgeCases:

    def test_empty_triangles_mesh(self):
        obj = Triangles([], [])

        data = TrianglesSerializer.serialize(obj)
        restored = TrianglesSerializer.deserialize(data)

        assert restored.vertices == []
        assert restored.triangles == []

    def test_vertices_no_triangles(self):
        obj = Triangles([(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)], [])

        data = TrianglesSerializer.serialize(obj)
        restored = TrianglesSerializer.deserialize(data)

        _assert_points_close(restored.vertices, [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)])
        assert restored.triangles == []

    def test_multiple_triangles_shared_vertices(self):
        vertices = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        triangles = [(0, 1, 2), (0, 2, 3)]
        obj = Triangles(vertices, triangles)

        data = TrianglesSerializer.serialize(obj)
        restored = TrianglesSerializer.deserialize(data)

        _assert_points_close(restored.vertices, vertices)
        assert restored.triangles == triangles

    def test_negative_coordinates(self):
        vertices = [(-5.5, -10.2), (-0.1, -100.0), (1.0, 2.0)]
        triangles = [(0, 1, 2)]
        obj = Triangles(vertices, triangles)

        data = TrianglesSerializer.serialize(obj)
        restored = TrianglesSerializer.deserialize(data)

        assert restored.vertices[0][0] == pytest.approx(-5.5)
        assert restored.vertices[0][1] == pytest.approx(-10.2)

    def test_very_close_vertices(self):
        vertices = [(0.0, 0.0), (1e-7, 1e-7), (2e-7, 0.0)]
        triangles = [(0, 1, 2)]
        obj = Triangles(vertices, triangles)

        data = TrianglesSerializer.serialize(obj)
        restored = TrianglesSerializer.deserialize(data)

        _assert_points_close(restored.vertices, vertices)
        assert restored.triangles == triangles


# ============================================================================ #
#  ERROR CASES
# ============================================================================ #

class TestTrianglesErrorCases:

    def test_deserialize_truncated_data(self):
        data = struct.pack("<I", 3)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 0.0)
        data += struct.pack("<ff", 0.0, 1.0)
        data += struct.pack("<I", 1)

        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(data)

    def test_deserialize_too_short(self):
        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(b"\x01\x00")

    def test_deserialize_empty_bytes(self):
        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(b"")

    def test_deserialize_inconsistent_size(self):
        data = struct.pack("<I", 2)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 1.0)
        data += struct.pack("<I", 1)
        data += struct.pack("<III", 0, 1, 2)
        data += b"\x00\x00\x00\x00"

        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(data)

    def test_invalid_triangle_indices(self):
        with pytest.raises(ValueError):
            Triangles([(0.0, 0.0), (1.0, 0.0)], [(0, 1, 2)])

    def test_repeated_triangle_vertices(self):
        with pytest.raises(ValueError):
            Triangles([(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)], [(0, 0, 2)])