"""
Reusable geometric objects for unit and integration tests.
"""

import pytest
from models.point import Point
from models.edge import Edge
from models.triangle import Triangle
from models.square import Square
from models.mesh import Mesh


# ---------------------------------------------------------------------------
# BASIC POINT FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def p0():
    return Point(0.0, 0.0)

@pytest.fixture
def p1():
    return Point(1.0, 0.0)

@pytest.fixture
def p2():
    return Point(0.0, 1.0)

@pytest.fixture
def p3():
    return Point(1.0, 1.0)


@pytest.fixture
def collinear_points():
    """Points lying on the line y = x."""
    return (Point(0, 0), Point(1, 1), Point(2, 2))


@pytest.fixture
def non_collinear_points():
    return (Point(0, 0), Point(1, 1), Point(1, 3))


# ---------------------------------------------------------------------------
# EDGE FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def edge01(p0, p1):
    return Edge(p0, p1)

@pytest.fixture
def edge12(p1, p2):
    return Edge(p1, p2)


# ---------------------------------------------------------------------------
# TRIANGLE FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def right_triangle(p0, p1, p2):
    """Reference right triangle."""
    return Triangle(p0, p1, p2)


@pytest.fixture
def square_two_triangles(p0, p3):
    """Return the two triangles that form the unit square."""
    s = Square(p0, p3)
    return s.to_triangles()


@pytest.fixture
def overlapping_triangles():
    """Two triangles that share overlapping internal area (invalid mesh)."""
    t1 = Triangle(Point(0,0), Point(2,0), Point(0,2))
    t2 = Triangle(Point(0.5,0.5), Point(3,0.5), Point(0.5,3))
    return t1, t2


# ---------------------------------------------------------------------------
# MESH FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_mesh(right_triangle):
    """A mesh with only one triangle."""
    return Mesh([right_triangle])


@pytest.fixture
def square_mesh(square_two_triangles):
    """Mesh for a square triangulated into two triangles."""
    return Mesh(square_two_triangles)
