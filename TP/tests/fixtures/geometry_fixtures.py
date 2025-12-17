"""
Reusable geometric objects for unit and integration tests.
"""

import pytest
from typing import List

from triangulator.models.point import Point
from triangulator.models.edge import Edge
from triangulator.models.triangle import Triangle
from triangulator.models.carre import Carre
from triangulator.models.mesh import Mesh


# ---------------------------------------------------------------------------
# BASIC POINT FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def p0() -> Point:
    return Point(0.0, 0.0)

@pytest.fixture
def p1() -> Point:
    return Point(1.0, 0.0)

@pytest.fixture
def p2() -> Point:
    return Point(0.0, 1.0)

@pytest.fixture
def p3() -> Point:
    return Point(1.0, 1.0)


@pytest.fixture
def collinear_points() -> List[Point]:
    """Points lying on the line y = x."""
    return [Point(0.0, 0.0), Point(1.0, 1.0), Point(2.0, 2.0)]


@pytest.fixture
def non_collinear_points() -> List[Point]:
    return [Point(0.0, 0.0), Point(1.0, 1.0), Point(1.0, 3.0)]


# ---------------------------------------------------------------------------
# EDGE FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def edge01(p0: Point, p1: Point) -> Edge:
    return Edge(p0, p1)

@pytest.fixture
def edge12(p1: Point, p2: Point) -> Edge:
    return Edge(p1, p2)


# ---------------------------------------------------------------------------
# TRIANGLE FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def right_triangle(p0: Point, p1: Point, p2: Point) -> Triangle:
    """Reference right triangle."""
    return Triangle(p0, p1, p2)


@pytest.fixture
def square_two_triangles(p0: Point, p3: Point) -> List[Triangle]:
    """Return the two triangles that form the unit square."""
    s = Square(p0, p3)
    # ensure a list is returned for easier iteration in tests
    return list(s.to_triangles())


@pytest.fixture
def overlapping_triangles() -> List[Triangle]:
    """Two triangles that share overlapping internal area (invalid mesh)."""
    t1 = Triangle(Point(0.0, 0.0), Point(2.0, 0.0), Point(0.0, 2.0))
    t2 = Triangle(Point(0.5, 0.5), Point(3.0, 0.5), Point(0.5, 3.0))
    return [t1, t2]


# ---------------------------------------------------------------------------
# MESH FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_mesh(right_triangle: Triangle) -> Mesh:
    """A mesh with only one triangle."""
    return Mesh([right_triangle])


@pytest.fixture
def square_mesh(square_two_triangles: List[Triangle]) -> Mesh:
    """Mesh for a square triangulated into two triangles."""
    return Mesh(square_two_triangles)
