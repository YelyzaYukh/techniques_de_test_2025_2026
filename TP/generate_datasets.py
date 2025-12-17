"""Dataset generator for testing PointSetManager + Triangulator.

Generates:
- Random PointSets (binary)
- Triangles (binary)
- PointSetID (UUID)
- JSONL dataset file containing all metadata

Optional: export binary files alongside JSON.

Usage:
    python generate_dataset.py --count 100 --out dataset.jsonl --export-binary
"""

import json
import random
import struct
import uuid
from pathlib import Path

############################
# Binary encoding helpers  #
############################


def encode_point_set(points):
    binary = struct.pack(">I", len(points))
    for x, y in points:
        binary += struct.pack(">ff", x, y)
    return binary


def encode_triangles(points, triangles):
    blob = encode_point_set(points)

    blob += struct.pack(">I", len(triangles))
    for a, b, c in triangles:
        blob += struct.pack(">III", a, b, c)
    return blob


############################
# Geometry generation      #
############################


def generate_random_points(n):
    """Generate n random 2D points inside [0,1]²."""
    return [(random.random(), random.random()) for _ in range(n)]


def triangulate(points):
    """Simple fan triangulation (same as Triangulator implementation)."""
    if len(points) < 3:
        return []
    tris = []
    for i in range(1, len(points) - 1):
        tris.append((0, i, i + 1))
    return tris


############################
# Dataset generation       #
############################


def generate_dataset_entry():
    """Generate one dataset entry with ID, PointSet, Triangles."""
    point_set_id = str(uuid.uuid4())
    n = random.randint(3, 30)

    points = generate_random_points(n)
    bin_points = encode_point_set(points)

    triangles = triangulate(points)
    bin_triangles = encode_triangles(points, triangles)

    return {
        "id": point_set_id,
        "points": points,
        "triangles": triangles,
        "binary_pointset": bin_points.hex(),
        "binary_triangles": bin_triangles.hex(),
    }


def generate_dataset(count, outfile, export_binary=False):
    outfile = Path(outfile)

    with outfile.open("w", encoding="utf8") as f:
        for _ in range(count):
            entry = generate_dataset_entry()
            f.write(json.dumps(entry) + "\n")

            if export_binary:
                pid = entry["id"]

                (outfile.parent / f"{pid}.pointset").write_bytes(
                    bytes.fromhex(entry["binary_pointset"])
                )

                (outfile.parent / f"{pid}.triangles").write_bytes(
                    bytes.fromhex(entry["binary_triangles"])
                )


############################
# CLI                     #
############################

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--out", type=str, default="dataset.jsonl")
    parser.add_argument("--export-binary", action="store_true")
    args = parser.parse_args()

    generate_dataset(args.count, args.out, args.export_binary)
    print(f"Dataset written to {args.out}")
