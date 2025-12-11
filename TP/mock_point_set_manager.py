"""
Mock PointSetManager server.

Implements the minimal API from point_set_manager.yml:

POST /point-sets
    Body: binary PointSet
    Response: JSON {"id": "<uuid>"}

GET /point-sets/<id>
    Response: binary PointSet OR 404

This mock stores everything in memory and is suitable for tests.
"""

from flask import Flask, request, jsonify, Response
import uuid

app = Flask(__name__)

# In-memory storage: id -> binary PointSet
POINT_SETS: dict[str, bytes] = {}


@app.route("/point-sets", methods=["POST"])
def upload_point_set():
    """Accepts a binary PointSet and returns a new PointSetID."""
    binary = request.data

    if not binary:
        return jsonify({"error": "Empty body"}), 400

    point_set_id = str(uuid.uuid4())
    POINT_SETS[point_set_id] = binary

    return jsonify({"id": point_set_id}), 201


@app.route("/point-sets/<point_set_id>", methods=["GET"])
def get_point_set(point_set_id: str):
    """Returns the binary PointSet or HTTP 404."""
    if point_set_id not in POINT_SETS:
        return jsonify({"error": "PointSet not found"}), 404

    return Response(POINT_SETS[point_set_id], content_type="application/octet-stream")


if __name__ == "__main__":
    app.run(port=5001, debug=True)
