import struct
import math
from typing import List, Tuple

# ============================================================================ #
#  CONSTANTS
# ============================================================================ #

# Maximum finite value representable by IEEE-754 single precision
FLOAT32_MAX = 3.4028234663852886e+38


# ============================================================================ #
#  DATA MODELS
# ============================================================================ #

class PointSet:
    """Internal representation of a 2D point set."""

    def __init__(self, points: List[Tuple[float, float]]):
        if points is None:
            raise ValueError("PointSet points cannot be None")

        if not isinstance(points, list):
            raise ValueError("Points must be a list")

        for p in points:
            if not isinstance(p, tuple) or len(p) != 2:
                raise ValueError("Each point must be a tuple (x, y)")
            if not isinstance(p[0], (int, float)) or not isinstance(p[1], (int, float)):
                raise ValueError("Point coordinates must be numeric")

        self.points = points

    def __eq__(self, other):
        if not isinstance(other, PointSet):
            return False
        return self.points == other.points


class Triangles:
    """Internal representation of triangles with shared vertices."""

    def __init__(self, vertices: List[Tuple[float, float]], triangles: List[Tuple[int, int, int]]):
        if vertices is None or triangles is None:
            raise ValueError("Vertices and triangles cannot be None")

        # Validate vertices
        if not isinstance(vertices, list):
            raise ValueError("vertices must be a list")
        for v in vertices:
            if not isinstance(v, tuple) or len(v) != 2:
                raise ValueError("Each vertex must be a tuple (x, y)")
            if not isinstance(v[0], (int, float)) or not isinstance(v[1], (int, float)):
                raise ValueError("Vertex coordinates must be numeric")

        # Validate triangles
        if not isinstance(triangles, list):
            raise ValueError("triangles must be a list")
        n_vertices = len(vertices)
        for t in triangles:
            if not isinstance(t, tuple) or len(t) != 3:
                raise ValueError("Each triangle must be a tuple of three indices")
            a, b, c = t
            if not all(isinstance(i, int) for i in (a, b, c)):
                raise ValueError("Triangle indices must be integers")
            # indices in range
            if a < 0 or b < 0 or c < 0 or a >= n_vertices or b >= n_vertices or c >= n_vertices:
                raise ValueError("Triangle index out of bounds")
            # cannot repeat vertices
            if a == b or b == c or a == c:
                raise ValueError("Triangle cannot repeat vertices")

        self.vertices = vertices
        self.triangles = triangles

    def __eq__(self, other):
        return (
            isinstance(other, Triangles)
            and self.vertices == other.vertices
            and self.triangles == other.triangles
        )


# ============================================================================ #
#  HELPERS
# ============================================================================ #

def _to_f32_clamped(x: float) -> float:
    """Convert to float32-representable finite value, clamping if needed."""
    fx = float(x)
    if not math.isfinite(fx):
        return math.copysign(FLOAT32_MAX, fx)
    if fx > FLOAT32_MAX:
        return FLOAT32_MAX
    if fx < -FLOAT32_MAX:
        return -FLOAT32_MAX
    return fx


# ============================================================================ #
#  POINTSET SERIALIZER
# ============================================================================ #

class PointSetSerializer:

    @staticmethod
    def serialize(pointset: PointSet) -> bytes:
        if not isinstance(pointset, PointSet):
            raise ValueError("serialize expects a PointSet object")

        n = len(pointset.points)
        out = bytearray()
        out += struct.pack("<I", n)
        for x, y in pointset.points:
            fx = _to_f32_clamped(x)
            fy = _to_f32_clamped(y)
            out += struct.pack("<ff", fx, fy)
        return bytes(out)

    @staticmethod
    def deserialize(data: bytes) -> PointSet:
        if not data or len(data) < 4:
            raise ValueError("Invalid binary data for PointSet")

        n = struct.unpack("<I", data[:4])[0]
        expected_size = 4 + 8 * n

        if len(data) != expected_size:
            raise ValueError("Inconsistent PointSet binary size")

        points = []
        offset = 4
        for _ in range(n):
            if offset + 8 > len(data):
                raise ValueError("Inconsistent PointSet binary size")
            x, y = struct.unpack("<ff", data[offset:offset + 8])
            points.append((float(x), float(y)))
            offset += 8

        return PointSet(points)


# ============================================================================ #
#  TRIANGLES SERIALIZER
# ============================================================================ #

class TrianglesSerializer:

    @staticmethod
    def serialize(triangles_obj: Triangles) -> bytes:
        if not isinstance(triangles_obj, Triangles):
            raise ValueError("serialize expects a Triangles object")

        n_vertices = len(triangles_obj.vertices)
        m_triangles = len(triangles_obj.triangles)

        out = bytearray()
        # Layout: <I n_vertices> <vertices...> <I m_triangles> <triangles...>
        out += struct.pack("<I", n_vertices)

        for x, y in triangles_obj.vertices:
            fx = _to_f32_clamped(x)
            fy = _to_f32_clamped(y)
            out += struct.pack("<ff", fx, fy)

        out += struct.pack("<I", m_triangles)
        for a, b, c in triangles_obj.triangles:
            out += struct.pack("<III", a, b, c)

        return bytes(out)

    @staticmethod
    def deserialize(data: bytes) -> Triangles:
        if not data or len(data) < 4:
            raise ValueError("Invalid binary data for Triangles")

        # Layout: <I n_vertices> <vertices...> <I m_triangles> <triangles...>
        n_vertices = struct.unpack("<I", data[:4])[0]
        offset = 4

        # read vertices
        vertices = []
        for _ in range(n_vertices):
            if offset + 8 > len(data):
                raise ValueError("Inconsistent Triangles binary size")
            x, y = struct.unpack("<ff", data[offset:offset + 8])
            vertices.append((float(x), float(y)))
            offset += 8

        # read triangle count
        if offset + 4 > len(data):
            raise ValueError("Inconsistent Triangles binary size")
        m_triangles = struct.unpack("<I", data[offset:offset + 4])[0]
        offset += 4

        # expected total size
        expected_size = 4 + 8 * n_vertices + 4 + 12 * m_triangles
        if len(data) != expected_size:
            raise ValueError("Inconsistent Triangles binary size")

        # read triangles
        triangles = []
        for _ in range(m_triangles):
            if offset + 12 > len(data):
                raise ValueError("Inconsistent Triangles binary size")
            a, b, c = struct.unpack("<III", data[offset:offset + 12])
            triangles.append((int(a), int(b), int(c)))
            offset += 12

        return Triangles(vertices, triangles)