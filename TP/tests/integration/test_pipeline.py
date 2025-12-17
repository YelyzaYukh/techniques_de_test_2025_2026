from triangulator.models.serialize import (
    PointSet,
    PointSetSerializer,
    Triangles,
    TrianglesSerializer,
)


def fake_triangulation(ps: PointSet):
    # minimal working triangulation: return a single triangle
    return Triangles(ps.points[:3], [(0, 1, 2)])


def test_pipeline_roundtrip():
    # Step 1 — initial PointSet
    points = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    ps = PointSet(points)

    # Step 2 — serialize
    binary = PointSetSerializer.serialize(ps)

    # Step 3 — send to triangulation service (simulated)
    restored = PointSetSerializer.deserialize(binary)

    # Step 4 — triangulate
    tri = fake_triangulation(restored)

    # Step 5 — serialize triangles
    tbin = TrianglesSerializer.serialize(tri)

    # Step 6 — restore
    restored_tri = TrianglesSerializer.deserialize(tbin)

    assert restored_tri.vertices == points
    assert restored_tri.triangles == [(0, 1, 2)]
