import struct


# ============================================================================ #
#  DATA MODELS
# ============================================================================ #

class PointSet:
    """Internal representation of a 2D point set."""

    def __init__(self, points):
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
        return isinstance(other, PointSet) and self.points == other.points


class Triangles:
    """Internal representation of triangles with shared vertices."""

    def __init__(self, vertices, triangles):
        if vertices is None or triangles is None:
            raise ValueError("Vertices and triangles cannot be None")

        # Validate vertices
        for v in vertices:
            if not isinstance(v, tuple) or len(v) != 2:
                raise ValueError("Vertex must be (x, y)")
            if not isinstance(v[0], (int, float)) or not isinstance(v[1], (int, float)):
                raise ValueError("Vertex coordinates must be numeric")

        # Validate triangles
        for t in triangles:
            if not isinstance(t, tuple) or len(t) != 3:
                raise ValueError("Triangle must be 3 indices")
            if not all(isinstance(i, int) for i in t):
                raise ValueError("Triangle indices must be integers")
            if len(set(t)) != 3:
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
#  POINTSET SERIALIZER
# ============================================================================ #

class PointSetSerializer:

    @staticmethod
    def serialize(pointset):
        if not isinstance(pointset, PointSet):
            raise ValueError("serialize expects a PointSet object")

        n = len(pointset.points)
        data = struct.pack("<I", n)

        for x, y in pointset.points:
            data += struct.pack("<ff", float(x), float(y))

        return data

    @staticmethod
    def deserialize(data: bytes):
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
                raise ValueError("Truncated PointSet data")
            x, y = struct.unpack("<ff", data[offset:offset+8])
            points.append((x, y))
            offset += 8

        return PointSet(points)


# ============================================================================ #
#  TRIANGLES SERIALIZER
# ============================================================================ #

class TrianglesSerializer:

    @staticmethod
    def serialize(triangles_obj):
        if not isinstance(triangles_obj, Triangles):
            raise ValueError("serialize expects a Triangles object")

        vertices = triangles_obj.vertices
        tri_list = triangles_obj.triangles

        # Part 1: vertices
        data = struct.pack("<I", len(vertices))
        for x, y in vertices:
            data += struct.pack("<ff", float(x), float(y))

        # Part 2: triangles
        data += struct.pack("<I", len(tri_list))

        for i1, i2, i3 in tri_list:
            if (
                i1 < 0 or i2 < 0 or i3 < 0
                or i1 >= len(vertices)
                or i2 >= len(vertices)
                or i3 >= len(vertices)
            ):
                raise ValueError("Triangle index out of bounds")

            data += struct.pack("<III", i1, i2, i3)

        return data

    @staticmethod
    def deserialize(data: bytes):
        if not data or len(data) < 4:
            raise ValueError("Invalid binary data for Triangles")

        offset = 0

        # Part 1: vertices
        n_vertices = struct.unpack("<I", data[offset:offset+4])[0]
        offset += 4

        vertices = []
        for _ in range(n_vertices):
            if offset + 8 > len(data):
                raise ValueError("Truncated vertex section")
            x, y = struct.unpack("<ff", data[offset:offset+8])
            vertices.append((x, y))
            offset += 8

        # Part 2: triangles count
        if offset + 4 > len(data):
            raise ValueError("Missing triangle count")

        n_triangles = struct.unpack("<I", data[offset:offset+4])[0]
        offset += 4

        triangles = []
        for _ in range(n_triangles):
            if offset + 12 > len(data):
                raise ValueError("Truncated triangle entry")
            i1, i2, i3 = struct.unpack("<III", data[offset:offset+12])
            offset += 12

            if (
                i1 >= n_vertices or
                i2 >= n_vertices or
                i3 >= n_vertices
            ):
                raise ValueError("Triangle index out of bounds")

            if len({i1, i2, i3}) != 3:
                raise ValueError("Triangle cannot have duplicate vertices")

            triangles.append((i1, i2, i3))

        return Triangles(vertices, triangles)