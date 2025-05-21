from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
ALLOWED_EXTENSIONS = {"pdf"}
DEBUG_MODE = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
SERVICE_PORT = int(os.environ.get("UPLOAD_SERVICE_PORT", 8050))

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"message": "No file part in the request"}, 400)
    file = request.files["file"]

    if file.filename == "":
        return jsonify({"message": "No selected file"}, 400)
    if file:
        filename = secure_filename(file.filename)
        print(filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        return jsonify({"message": f"File {filename} uploaded successfully"}, 200)
    else:
        return jsonify({"message": "File type not allowed"}, 400)


@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=False, mimetype="application/pdf")
    else:
        return jsonify({"message": "File not found"}, 404)


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for the upload service.
    """
    return jsonify({"status": "healthy", "service": "upload_service"}), 200


if __name__ == "__main__":
    app.run(debug=DEBUG_MODE, port=SERVICE_PORT, host="0.0.0.0")
