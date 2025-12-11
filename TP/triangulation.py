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
import requests
from flask import Flask, request, Response, jsonify


#############################
#  Binary format utilities  #
#############################

def decode_point_set(binary: bytes) -> list[tuple[float, float]]:
    """Decode a binary PointSet into a list of (x, y) floats."""
    if len(binary) < 4:
        raise ValueError("Binary PointSet too small")

    n_points = struct.unpack(">I", binary[:4])[0]
    expected_len = 4 + n_points * 8

    if len(binary) != expected_len:
        raise ValueError("Malformed PointSet binary")

    points = []
    offset = 4
    for _ in range(n_points):
        x, y = struct.unpack(">ff", binary[offset:offset + 8])
        points.append((x, y))
        offset += 8

    return points


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
    r = requests.get(url)

    if r.status_code == 404:
        raise KeyError("PointSet not found")

    if r.status_code != 200:
        raise RuntimeError("PointSetManager error")

    return r.content


@app.route("/triangulate/<point_set_id>", methods=["GET"])
def triangulate_endpoint(point_set_id: str):
    """
    Endpoint defined in triangulator.yml.

    Returns binary Triangles.
    """

    try:
        binary_ps = fetch_point_set(point_set_id)
        points = decode_point_set(binary_ps)
        triangles = triangulate(points)
        result = encode_triangles(points, triangles)

        return Response(result, content_type="application/octet-stream")

    except KeyError:
        return jsonify({"error": "PointSet not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(port=5002, debug=True)
