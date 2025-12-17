"""Triangulator micro-service.

Implements:
- Binary decoding of PointSet
- Triangulation algorithm
- Binary encoding of Triangles
- Flask server exposing the OpenAPI operations

This implementation uses a simple O(n) fan triangulation
because correctness matters more than geometric optimality.
"""

from __future__ import annotations

import struct
import urllib.error
import urllib.request

from flask import Flask, Response, jsonify
from triangulator.models.serialize import (
    Triangles,
    TrianglesSerializer,
)

# ============================================================================ #
#  CONSTANTS
# ============================================================================ #

POINT_SET_MANAGER_URL = "http://localhost:5001/point-sets"
"""URL of PointSetManager API for fetching PointSets."""


# ============================================================================ #
#  BINARY FORMAT UTILITIES
# ============================================================================ #


def decode_point_set(binary: bytes) -> list[tuple[float, float]]:
    """Decode binary PointSet to list of points.

    Parses little-endian binary format with uint32 count followed by
    float32 (x, y) pairs. Validates total size consistency.

    Args:
        binary (bytes): Binary data in PointSet format

    Returns:
        list[tuple[float, float]]: List of (x, y) coordinate tuples

    Raises:
        ValueError: If binary is None, malformed, or has inconsistent size

    Example:
        >>> binary = b'\\x02\\x00\\x00\\x00' + b'\\x00' * 16
        >>> points = decode_point_set(binary)
        >>> len(points)
        2

    """
    if binary is None:
        raise ValueError("PointSet data is None")

    if not isinstance(binary, bytes) or len(binary) < 4:
        raise ValueError("Malformed PointSet binary")

    try:
        n = struct.unpack("<I", binary[:4])[0]
        expected_size = 4 + 8 * n

        if len(binary) != expected_size:
            raise ValueError("Malformed PointSet binary")

        points = []
        offset = 4
        for _ in range(n):
            x, y = struct.unpack("<ff", binary[offset : offset + 8])
            points.append((float(x), float(y)))
            offset += 8

        return points
    except (struct.error, ValueError) as e:
        raise ValueError(f"Malformed PointSet binary: {e}") from e


def encode_point_set(points: list[tuple[float, float]]) -> bytes:
    """Encode a list of (x, y) float points into binary PointSet format.

    Creates little-endian binary with uint32 count and float32 coordinates.

    Args:
        points (list[tuple[float, float]]): List of (x, y) coordinate tuples

    Returns:
        bytes: Binary data in PointSet format (little-endian)

    Raises:
        struct.error: If packing fails (should not occur for valid floats)

    Example:
        >>> points = [(0.0, 0.0), (1.0, 1.0)]
        >>> binary = encode_point_set(points)
        >>> len(binary)
        20

    """
    n = len(points)
    binary = struct.pack("<I", n)
    for x, y in points:
        binary += struct.pack("<ff", x, y)
    return binary


def encode_triangles(
    points: list[tuple[float, float]], triangles: list[tuple[int, int, int]]
) -> bytes:
    """Encode Triangles in binary format.

    Combines PointSet encoding with triangle indices:
    - PointSet header and vertices
    - uint32: number of triangles
    - For each triangle: 3 uint32 indices (12 bytes total per triangle)

    Args:
        points (list[tuple[float, float]]): List of vertex coordinates
        triangles (list[tuple[int, int, int]]): List of (i, j, k) index tuples

    Returns:
        bytes: Binary Triangles data (little-endian)

    Raises:
        struct.error: If packing fails

    Example:
        >>> points = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
        >>> triangles = [(0, 1, 2)]
        >>> binary = encode_triangles(points, triangles)
        >>> len(binary)
        56

    """
    blob = encode_point_set(points)

    n_tri = len(triangles)
    blob += struct.pack("<I", n_tri)

    for a, b, c in triangles:
        blob += struct.pack("<III", a, b, c)

    return blob


# ============================================================================ #
#  TRIANGULATION
# ============================================================================ #


def triangulate(points: list[tuple[float, float]]) -> list[tuple[int, int, int]]:
    """Perform simple fan triangulation on a set of points.

    Creates triangles using fan method: (p0, pi, pi+1) for i in [1..n-2].
    This is not Delaunay triangulation, but generates valid, deterministic
    output suitable for testing.

    Args:
        points (list[tuple[float, float]]): List of (x, y) coordinate tuples

    Returns:
        list[tuple[int, int, int]]: List of triangle index tuples (i, j, k)

    Raises:
        None

    Example:
        >>> points = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)]
        >>> triangles = triangulate(points)
        >>> len(triangles)
        2
        >>> triangles
        [(0, 1, 2), (0, 2, 3)]

    """
    if len(points) < 3:
        return []

    tris = []
    for i in range(1, len(points) - 1):
        tris.append((0, i, i + 1))

    return tris


# ============================================================================ #
#  FLASK SERVICE
# ============================================================================ #

app = Flask(__name__)


def fetch_point_set(point_set_id: str) -> bytes:
    """Fetch binary PointSet from PointSetManager API.

    Makes HTTP GET request to PointSetManager and returns binary response.
    This function is designed to be easily mocked in unit tests.

    Args:
        point_set_id (str): Unique identifier of the PointSet to fetch

    Returns:
        bytes: Binary PointSet data

    Raises:
        urllib.error.HTTPError: If PointSet not found (404) or server error
        ValueError: If HTTP response status is not 200

    Example:
        >>> binary = fetch_point_set("abc123")
        >>> len(binary)
        20

    """
    url = f"{POINT_SET_MANAGER_URL}/{point_set_id}"
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                raise ValueError("PointSetManager error")
            return response.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError("PointSet not found") from e
        raise


@app.route("/triangulate/<point_set_id>", methods=["GET"])
def triangulate_endpoint(point_set_id: str) -> tuple[Response | dict, int]:
    """HTTP endpoint for triangulation.

    Fetches PointSet by ID, triangulates, and returns binary Triangles.
    Defined in OpenAPI specification (triangulator.yml).

    Args:
        point_set_id (str): ID of PointSet to triangulate

    Returns:
        tuple[Response | dict, int]: (binary Response or error JSON, HTTP status)

    Raises:
        None (all exceptions caught and converted to HTTP responses)

    Example:
        >>> response = client.get("/triangulate/test123")
        >>> response.status_code
        200

    """
    try:
        binary_ps = fetch_point_set(point_set_id)

        if binary_ps is None:
            return jsonify({"error": "PointSet not found"}), 404

        points = decode_point_set(binary_ps)

        if len(points) < 3:
            return jsonify(
                {"error": "At least 3 points required for triangulation"}
            ), 400

        triangles = triangulate(points)

        tri_obj = Triangles(points, triangles)
        binary_tri = TrianglesSerializer.serialize(tri_obj)

        return Response(binary_tri, content_type="application/octet-stream", status=200)

    except ValueError as e:
        print(f"Error in triangulation: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(port=5002, debug=True)
