"""Tests des propriétés générales de la sérialisation binaire.

Auteur: Yelyzaveta YUKHNOVA

"""

import random

import pytest
from triangulator.models.serialize import PointSet, PointSetSerializer

# ============================================================================ #
#  DETERMINISM & FORMAT CONSISTENCY
# ============================================================================ #


class TestSerializationProperties:
    def test_deterministic(self):
        ps = PointSet([(1.0, 2.0), (3.0, 4.0)])

        d1 = PointSetSerializer.serialize(ps)
        d2 = PointSetSerializer.serialize(ps)

        assert d1 == d2

    def test_compact_format(self):
        points = [(float(i), float(i)) for i in range(10)]
        ps = PointSet(points)

        data = PointSetSerializer.serialize(ps)
        assert len(data) == 4 + 10 * 8

    def test_endianness(self):
        ps = PointSet([(1.0, 2.0)])
        data = PointSetSerializer.serialize(ps)

        assert data[0] == 1
        assert data[1] == 0
        assert data[2] == 0
        assert data[3] == 0


# ============================================================================ #
#  RANDOMIZED FUZZ TESTING
# ============================================================================ #


class TestRandomRoundtrip:
    def test_random_roundtrip_pointset(self):
        for _ in range(50):
            pts = [
                (random.uniform(-1e6, 1e6), random.uniform(-1e6, 1e6))
                for _ in range(random.randint(0, 50))
            ]

            ps = PointSet(pts)
            data = PointSetSerializer.serialize(ps)
            restored = PointSetSerializer.deserialize(data)

            # compare elementwise with tolerance because serialization uses float32
            assert len(restored.points) == len(ps.points)
            for (rx, ry), (ox, oy) in zip(restored.points, ps.points):
                assert rx == pytest.approx(ox)
                assert ry == pytest.approx(oy)
