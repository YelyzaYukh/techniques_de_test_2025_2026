"""Tests unitaires pour la sérialisation/désérialisation binaire des Triangles.

Auteur: Yelyzaveta YUKHNOVA

"""

import struct
import pytest

from models.serialize import Triangles, TrianglesSerializer


# ============================================================================ #
#  BASIC TESTS
# ============================================================================ #

class TestTrianglesSerialization:

    def test_serialize_simple_triangle(self):
        vertices = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
        tri = Triangles(vertices, [(0, 1, 2)])

        data = TrianglesSerializer.serialize(tri)

        assert struct.unpack("<I", data[:4])[0] == 3

        offset = 4 + 3 * 8
        assert struct.unpack("<I", data[offset:offset+4])[0] == 1

        assert struct.unpack("<III", data[offset+4:offset+16]) == (0, 1, 2)

    def test_deserialize_simple_triangle(self):
        data = struct.pack("<I", 3)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 0.0)
        data += struct.pack("<ff", 0.0, 1.0)
        data += struct.pack("<I", 1)
        data += struct.pack("<III", 0, 1, 2)

        tri = TrianglesSerializer.deserialize(data)

        assert tri.vertices == [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
        assert tri.triangles == [(0, 1, 2)]

    def test_roundtrip(self):
        vertices = [(0, 0), (1, 0), (1, 1), (0, 1)]
        triangles = [(0, 1, 2), (0, 2, 3)]
        original = Triangles(vertices, triangles)

        data = TrianglesSerializer.serialize(original)
        restored = TrianglesSerializer.deserialize(data)

        assert restored == original

    @pytest.mark.parametrize("count", [1, 5, 10])
    def test_various_triangle_counts(self, count):
        vertices = [(float(i), float(i)) for i in range(count + 2)]
        triangle_list = [(i, i+1, i+2) for i in range(count)]

        tri = Triangles(vertices, triangle_list)
        data = TrianglesSerializer.serialize(tri)
        restored = TrianglesSerializer.deserialize(data)

        assert len(restored.triangles) == count


# ============================================================================ #
#  EDGE CASES
# ============================================================================ #

class TestTrianglesEdgeCases:

    def test_empty_triangles(self):
        tri = Triangles([(0,0), (1,1)], [])
        data = TrianglesSerializer.serialize(tri)
        restored = TrianglesSerializer.deserialize(data)

        assert restored.vertices == [(0,0), (1,1)]
        assert restored.triangles == []

    def test_empty_vertices_and_triangles(self):
        tri = Triangles([], [])
        data = TrianglesSerializer.serialize(tri)
        restored = TrianglesSerializer.deserialize(data)

        assert restored.vertices == []
        assert restored.triangles == []

    def test_shared_vertices(self):
        vertices = [(0,0), (1,0), (0.5,1)]
        triangles = [(0,1,2), (1,2,0)]
        tri = Triangles(vertices, triangles)

        data = TrianglesSerializer.serialize(tri)
        restored = TrianglesSerializer.deserialize(data)

        assert restored == tri


# ============================================================================ #
#  ERROR CASES
# ============================================================================ #

class TestTrianglesErrorCases:

    def test_truncated_vertices(self):
        data = struct.pack("<I", 3)
        data += struct.pack("<ff", 0.0, 0.0)

        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(data)

    def test_truncated_triangles(self):
        data = struct.pack("<I", 3)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 0.0)
        data += struct.pack("<ff", 0.0, 1.0)
        data += struct.pack("<I", 2)          # claim 2 triangles
        data += struct.pack("<III", 0,1,2)    # only one

        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(data)

    def test_out_of_bounds_indices(self):
        data = struct.pack("<I", 3)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 0.0)
        data += struct.pack("<ff", 0.0, 1.0)
        data += struct.pack("<I", 1)
        data += struct.pack("<III", 0, 1, 5)

        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(data)

    def test_negative_indices(self):
        data = struct.pack("<I", 3)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 0.0)
        data += struct.pack("<ff", 0.0, 1.0)
        data += struct.pack("<I", 1)
        data += struct.pack("<III", 0, 1, 4294967295)  # unsigned wrap → -1

        with pytest.raises(ValueError):
            TrianglesSerializer.deserialize(data)

    def test_duplicate_indices(self):
        vertices = [(0,0), (1,0), (0,1)]
        triangles = [(0,0,2)]  # invalid triangle

        with pytest.raises(ValueError):
            TrianglesSerializer.serialize(Triangles(vertices, triangles))

    def test_triangle_wrong_length(self):
        vertices = [(0,0), (1,0), (0,1)]
        triangles = [(0,1)]  # only 2 indices

        with pytest.raises(ValueError):
            TrianglesSerializer.serialize(Triangles(vertices, triangles))

    def test_non_integer_index(self):
        vertices = [(0,0), (1,0), (0,1)]
        triangles = [(0, "a", 2)]

        with pytest.raises(ValueError):
            TrianglesSerializer.serialize(Triangles(vertices, triangles))