"""Binary serialization module for geometric primitives.

This module provides classes and serializers for converting between Python
geometric objects (PointSet, Triangles) and their binary representations
according to IEEE-754 single-precision format.

Auteur: Yelyzaveta YUKHNOVA
"""

import math
import struct

# ============================================================================ #
#  CONSTANTS
# ============================================================================ #

FLOAT32_MAX = 3.4028234663852886e38
"""Maximum finite value representable by IEEE-754 single precision."""


# ============================================================================ #
#  HELPERS
# ============================================================================ #


def _to_f32_clamped(x: float) -> float:
    """Convert float to float32-representable finite value with clamping.

    Prevents struct.pack overflow by clamping very large values to FLOAT32_MAX.
    Handles infinities by converting them to signed FLOAT32_MAX.

    Args:
        x: Input float value

    Returns:
        float: Value safely convertible to IEEE-754 single precision

    """
    fx = float(x)
    if not math.isfinite(fx):
        return math.copysign(FLOAT32_MAX, fx)
    if fx > FLOAT32_MAX:
        return FLOAT32_MAX
    if fx < -FLOAT32_MAX:
        return -FLOAT32_MAX
    return fx


# ============================================================================ #
#  DATA MODELS
# ============================================================================ #


class PointSet:
    """Represents a set of 2D points.

    A PointSet is an immutable collection of (x, y) coordinate pairs.
    Used as input for triangulation algorithms.

    Attributes:
        points (List[Tuple[float, float]]): List of (x, y) coordinate tuples

    """

    def __init__(self, points: list[tuple[float, float]]):
        """Initialize a PointSet with validation.

        Args:
            points: List of tuples, each containing (x, y) float coordinates

        Raises:
            ValueError: If points is None, not a list, or contains invalid tuples

        """
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
        """Check equality with another PointSet.

        Args:
            other: Object to compare with

        Returns:
            bool: True if other is a PointSet with identical points

        """
        if not isinstance(other, PointSet):
            return False
        return self.points == other.points

    def __repr__(self):
        """Return string representation of PointSet.

        Returns:
            str: Representation showing number of points

        """
        return f"PointSet({len(self.points)} points)"


class Triangles:
    """Represents a triangulated mesh with shared vertices.

    A Triangles object stores vertices (shared 2D points) and triangles
    (references to vertex indices). This enables compact storage of meshes.

    Attributes:
        vertices (List[Tuple[float, float]]): Shared vertex coordinates
        triangles (List[Tuple[int, int, int]]): Triangle vertex index tuples

    """

    def __init__(
        self, vertices: list[tuple[float, float]], triangles: List[Tuple[int, int, int]]
    ):
        """Initialize a Triangles mesh with validation.

        Validates that:
        - All vertex indices are within bounds
        - No triangle repeats the same vertex (degenerate triangles forbidden)
        - All coordinates are numeric

        Args:
            vertices: List of (x, y) coordinate tuples for vertices
            triangles: List of (i, j, k) index tuples referencing vertices

        Raises:
            ValueError: If validation fails or data is malformed

        """
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
            if (
                a < 0
                or b < 0
                or c < 0
                or a >= n_vertices
                or b >= n_vertices
                or c >= n_vertices
            ):
                raise ValueError("Triangle index out of bounds")
            # cannot repeat vertices
            if a == b or b == c or a == c:
                raise ValueError("Triangle cannot repeat vertices")

        self.vertices = vertices
        self.triangles = triangles

    def __eq__(self, other):
        """Check equality with another Triangles object.

        Args:
            other: Object to compare with

        Returns:
            bool: True if vertices and triangles match exactly

        """
        return (
            isinstance(other, Triangles)
            and self.vertices == other.vertices
            and self.triangles == other.triangles
        )

    def __repr__(self):
        """Return string representation of Triangles.

        Returns:
            str: Representation showing vertex and triangle counts

        """
        return (
            f"Triangles({len(self.vertices)} vertices, {len(self.triangles)} triangles)"
        )


# ============================================================================ #
#  POINTSET SERIALIZER
# ============================================================================ #


class PointSetSerializer:
    """Serialize/deserialize PointSet objects to/from binary format.

    Binary format (little-endian):
        <I n>           - uint32: number of points
        <ff x1 y1>      - float32 x, float32 y for point 1
        <ff x2 y2>      - float32 x, float32 y for point 2
        ...
    """

    @staticmethod
    def serialize(pointset: PointSet) -> bytes:
        """Convert a PointSet to binary representation.

        Args:
            pointset: PointSet object to serialize

        Returns:
            bytes: Binary data in little-endian format

        Raises:
            ValueError: If pointset is not a PointSet instance

        """
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
        """Convert binary data to a PointSet object.

        Args:
            data: Binary bytes in PointSet format

        Returns:
            PointSet: Reconstructed PointSet object

        Raises:
            ValueError: If data is malformed or incomplete

        """
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
            x, y = struct.unpack("<ff", data[offset : offset + 8])
            points.append((float(x), float(y)))
            offset += 8

        return PointSet(points)


# ============================================================================ #
#  TRIANGLES SERIALIZER
# ============================================================================ #


class TrianglesSerializer:
    """Serialize/deserialize Triangles objects to/from binary format.

    Binary format (little-endian):
        <I n_vertices>          - uint32: number of vertices
        <ff x1 y1>              - float32 x, float32 y for vertex 1
        <ff x2 y2>              - float32 x, float32 y for vertex 2
        ...
        <I n_triangles>         - uint32: number of triangles
        <III i1 j1 k1>          - uint32 i, uint32 j, uint32 k for triangle 1
        <III i2 j2 k2>          - uint32 i, uint32 j, uint32 k for triangle 2
        ...
    """

    @staticmethod
    def serialize(triangles_obj: Triangles) -> bytes:
        """Convert a Triangles mesh to binary representation.

        Args:
            triangles_obj: Triangles object to serialize

        Returns:
            bytes: Binary data in little-endian format

        Raises:
            ValueError: If triangles_obj is not a Triangles instance

        """
        if not isinstance(triangles_obj, Triangles):
            raise ValueError("serialize expects a Triangles object")

        n_vertices = len(triangles_obj.vertices)
        m_triangles = len(triangles_obj.triangles)

        out = bytearray()
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
        """Convert binary data to a Triangles object.

        Args:
            data: Binary bytes in Triangles format

        Returns:
            Triangles: Reconstructed Triangles object

        Raises:
            ValueError: If data is malformed, inconsistent, or incomplete

        """
        if not data or len(data) < 4:
            raise ValueError("Invalid binary data for Triangles")

        n_vertices = struct.unpack("<I", data[:4])[0]
        offset = 4

        # read vertices
        vertices = []
        for _ in range(n_vertices):
            if offset + 8 > len(data):
                raise ValueError("Inconsistent Triangles binary size")
            x, y = struct.unpack("<ff", data[offset : offset + 8])
            vertices.append((float(x), float(y)))
            offset += 8

        # read triangle count
        if offset + 4 > len(data):
            raise ValueError("Inconsistent Triangles binary size")
        m_triangles = struct.unpack("<I", data[offset : offset + 4])[0]
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
            a, b, c = struct.unpack("<III", data[offset : offset + 12])
            triangles.append((int(a), int(b), int(c)))
            offset += 12

        return Triangles(vertices, triangles)
