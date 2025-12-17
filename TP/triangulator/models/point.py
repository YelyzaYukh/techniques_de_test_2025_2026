import math


class Point:
    """A simple 2D geometric point with float coordinates."""

    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)

    # --------------------------------------------------------------
    # Equality & hashing
    # --------------------------------------------------------------

    def __eq__(self, other):
        """Compare points with float tolerance."""
        return (
            isinstance(other, Point)
            and math.isclose(self.x, other.x, rel_tol=1e-9, abs_tol=1e-12)
            and math.isclose(self.y, other.y, rel_tol=1e-9, abs_tol=1e-12)
        )

    def __hash__(self):
        """Hashable so Point can be used in sets and dict keys."""
        return hash((round(self.x, 12), round(self.y, 12)))

    # --------------------------------------------------------------
    # Nice representation
    # --------------------------------------------------------------

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

    # --------------------------------------------------------------
    # Conversions
    # --------------------------------------------------------------

    def as_tuple(self):
        """Return (x, y) tuple."""
        return (self.x, self.y)

    # --------------------------------------------------------------
    # Vector helpers
    # --------------------------------------------------------------

    def distance_to(self, other: "Point") -> float:
        """Euclidean distance."""
        return math.hypot(self.x - other.x, self.y - other.y)

    def __sub__(self, other):
        """Vector subtraction: P - Q."""
        return Point(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        """Vector addition: P + Q."""
        return Point(self.x + other.x, self.y + other.y)

    def dot(self, other: "Point") -> float:
        """Dot product."""
        return self.x * other.x + self.y * other.y

    def cross(self, other: "Point") -> float:
        """2D cross product (scalar)."""
        return self.x * other.y - self.y * other.x
