from flask import Flask, request
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get secret key from .env
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY not found in environment variables")

# Initialize app
app = Flask(__name__)

# Set upload folder relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "InputNotes")

# Config
ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024 * 1024  # 1 GB

app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_BYTES

# Ensure folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def is_allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["POST"])
def upload_file():
    # Check secret key
    incoming_key = request.form.get("key")
    if incoming_key != SECRET_KEY:
        return "Unauthorized", 401

    # Check file exists
    if "file" not in request.files:
        return "No file part", 400

    file = request.files["file"]

    if not file or file.filename == "":
        return "No selected file", 400

    # Check file type
    if not is_allowed_file(file.filename):
        return "Only PDF files are allowed", 400

    # Secure filename + timestamp
    safe_name = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{safe_name}"

    save_path = os.path.join(UPLOAD_FOLDER, filename)

    # Save file
    file.save(save_path)

    print(f"Saved: {save_path}")

    return "Upload successful", 200


# Handle oversized files
@app.errorhandler(413)
def too_large(_error):
    return "File too large. Max size is 1 GB.", 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)