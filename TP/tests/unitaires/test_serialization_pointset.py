"""Tests unitaires pour la sérialisation/désérialisation binaire des PointSet.

Auteur: Yelyzaveta YUKHNOVA

Ce module teste les conversions entre structures Python et format binaire
pour PointSet et Triangles selon la spécification OpenAPI.
"""

import struct
import pytest

from models.serialize import PointSet, PointSetSerializer


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

        assert struct.unpack("<ff", data[4:12]) == (0.0, 0.0)
        assert struct.unpack("<ff", data[12:20]) == (1.0, 0.0)
        assert struct.unpack("<ff", data[20:28]) == (0.0, 1.0)

    def test_deserialize_simple_pointset(self):
        data = struct.pack("<I", 3)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 0.0)
        data += struct.pack("<ff", 0.0, 1.0)

        ps = PointSetSerializer.deserialize(data)

        assert ps.points == [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]

    def test_roundtrip(self):
        original = PointSet([(1.5, 2.5), (-1.0, 3.0), (0.0, 0.0)])

        data = PointSetSerializer.serialize(original)
        restored = PointSetSerializer.deserialize(data)

        assert restored == original

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
        assert restored.points == points


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

        assert restored.points[0] == pytest.approx((-5.5, -10.2))

    def test_extreme_float_values(self):
        import sys
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

        assert restored.points == points


# ============================================================================ #
#  ERROR CASES
# ============================================================================ #

class TestPointSetErrorCases:

    def test_deserialize_truncated(self):
        data = struct.pack("<I", 3)
        data += struct.pack("<ff", 0.0, 0.0)
        data += struct.pack("<ff", 1.0, 1.0)

        with pytest.raises(ValueError):
            PointSetSerializer.deserialize(data)

    def test_deserialize_too_short(self):
        with pytest.raises(ValueError):
            PointSetSerializer.deserialize(b"\x01\x00")

    def test_empty_bytes(self):
        with pytest.raises(ValueError):
            PointSetSerializer.deserialize(b"")

    def test_inconsistent_size(self):
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