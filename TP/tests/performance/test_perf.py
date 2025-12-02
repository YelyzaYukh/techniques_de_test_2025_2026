import time
from models.serialize import PointSet, PointSetSerializer


def test_large_pointset_serialization_performance():
    # 50 000 points
    points = [(float(i), float(i)) for i in range(50_000)]
    ps = PointSet(points)

    t0 = time.perf_counter()
    data = PointSetSerializer.serialize(ps)
    duration = time.perf_counter() - t0

    assert len(data) == 4 + 50_000 * 8
    assert duration < 0.5  # should serialize fast
