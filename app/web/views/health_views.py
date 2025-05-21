from flask import Blueprint, jsonify

bp = Blueprint("health", __name__, url_prefix="/api")


@bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for the backend service.
    """
    return jsonify({"status": "healthy", "service": "backend"}), 200
