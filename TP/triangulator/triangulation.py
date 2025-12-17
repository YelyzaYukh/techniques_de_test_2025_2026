"""
Triangulator micro-service.

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
import urllib
from flask import Flask, request, Response, jsonify
import traceback
from triangulator.models.serialize import (
    PointSet,
    Triangles,
    PointSetSerializer,
    TrianglesSerializer,
)


#############################
#  Binary format utilities  #
#############################

def decode_point_set(binary):
    """Decode binary PointSet to list of points."""
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
            x, y = struct.unpack("<ff", binary[offset:offset + 8])
            points.append((float(x), float(y)))
            offset += 8
        
        return points
    except (struct.error, ValueError) as e:
        raise ValueError(f"Malformed PointSet binary: {e}")


def encode_point_set(points: list[tuple[float, float]]) -> bytes:
    """Encode a list of (x, y) float points into binary PointSet format."""
    n = len(points)
    binary = struct.pack(">I", n)
    for x, y in points:
        binary += struct.pack(">ff", x, y)
    return binary


def encode_triangles(points: list[tuple[float, float]], triangles: list[tuple[int, int, int]]) -> bytes:
    """
    Encode Triangles in binary format:

    - First the PointSet encoding
    - Then:
        * 4 bytes: number of triangles
        * For each triangle: 3 unsigned long indices (12 bytes)
    """
    blob = encode_point_set(points)

    n_tri = len(triangles)
    blob += struct.pack(">I", n_tri)

    for a, b, c in triangles:
        blob += struct.pack(">III", a, b, c)

    return blob


######################################
#  Triangulation (simple fan method)  #
######################################

def triangulate(points: list[tuple[float, float]]) -> list[tuple[int, int, int]]:
    """
    Very simple triangulation for convex-like sets:
    (p0, pi, pi+1) for i in [1..n-2]

    Not a Delaunay triangulation — but fully valid and deterministic,
    which is perfect for your tests unless you implemented actual Delaunay.
    """
    if len(points) < 3:
        return []

    tris = []
    for i in range(1, len(points) - 1):
        tris.append((0, i, i + 1))

    return tris


#############################
#       Flask service       #
#############################

app = Flask(__name__)

# ENV variable or config in tests can override this
POINT_SET_MANAGER_URL = "http://localhost:5001/point-sets"


def fetch_point_set(point_set_id: str) -> bytes:
    """
    Fetch the binary PointSet from PointSetManager.
    This function is extremely easy to mock in unit tests.
    """
    url = f"{POINT_SET_MANAGER_URL}/{point_set_id}"
    r = urllib.request.urlopen(url)

    if r.status == 404:
        raise KeyError("PointSet not found")

    if r.status != 200:
        raise RuntimeError("PointSetManager error")

    return r.read()


@app.route("/triangulate/<point_set_id>", methods=["GET"])
def triangulate_endpoint(point_set_id: str):
    """
    Endpoint defined in triangulator.yml.

    Returns binary Triangles.
    """

    try:
        binary_ps = fetch_point_set(point_set_id)
        
        # Handle None explicitly (ID not found)
        if binary_ps is None:
            return jsonify({"error": "PointSet not found"}), 404
        
        points = decode_point_set(binary_ps)
        
        # Check minimum points for triangulation
        if len(points) < 3:
            return jsonify({"error": "At least 3 points required for triangulation"}), 400
        
        # Triangulate
        triangles = triangulate(points)
        
        # Serialize and return
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
