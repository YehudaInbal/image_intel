from flask import Flask, render_template, request, send_file
import os
import re
import tempfile

from timeline import create_timeline
from analyzer import analyze
from report import create_report
from pdf_export import export_report_to_pdf
from extractor import extract_all
from map_view import create_map
from mail_sender import send_pdf_email
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from pathlib import Path
import re
import base64
import io
from detector import detect_faces_in_image
import extractor
print("APP USING EXTRACTOR FILE:", extractor.__file__, flush=True)



def sanitize_to_ascii(text):
    """
    Removes any non-ASCII characters (like Hebrew) from the string.
    This ensures the output contains only English letters, numbers, and symbols.
    """
    if not text:
        return text
    return re.sub(r'[^\x20-\x7E]', '', text).strip()


def get_gps_dict(data: dict):
    """
    Extracts GPS-related tags from the general metadata dictionary.
    """
    gps_readable = {}
    for key, value in data.items():
        if key.startswith("GPS"):
            gps_readable[key] = value
    return gps_readable


def has_gps(data: dict):
    """Checks if both latitude and longitude exist in the data."""
    gps_readable = get_gps_dict(data)
    return "GPSLatitude" in gps_readable and "GPSLongitude" in gps_readable


def latitude(data: dict):
    """Extracts and converts latitude to decimal format."""
    gps_data = get_gps_dict(data)
    lat_values = gps_data.get("GPSLatitude")
    ref = gps_data.get("GPSLatitudeRef")

    if lat_values and ref:
        return dms_to_decimal(lat_values, ref)
    return None


def longitude(data: dict):
    """Extracts and converts longitude to decimal format."""
    gps_data = get_gps_dict(data)
    lon_values = gps_data.get("GPSLongitude")
    ref = gps_data.get("GPSLongitudeRef")

    if lon_values and ref:
        return dms_to_decimal(lon_values, ref)
    return None


def datatime(data: dict):
    """Searches for the original timestamp in the metadata."""
    dt = data.get("DateTimeOriginal") or data.get("DateTimeDigitized") or data.get("DateTime")
    if dt is not None:
        return str(dt).strip()
    return None


def camera_make(data: dict):
    """Extracts camera manufacturer."""
    make = data.get("Make")
    if make is not None:
        return str(make).strip('\x00').strip()
    return None


def camera_model(data: dict):
    """Extracts camera model name."""
    model = data.get("Model")
    if model is not None:
        return str(model).strip('\x00').strip()
    return None


def dms_to_decimal(dms_tuple, ref):
    """Converts Degrees/Minutes/Seconds tuple to decimal float."""
    try:
        degrees = float(dms_tuple[0])
        minutes = float(dms_tuple[1])
        seconds = float(dms_tuple[2])

        decimal = degrees + minutes / 60 + seconds / 3600
        if ref in [b'S', b'W', 'S', 'W']:
            decimal = -decimal
        return decimal
    except (TypeError, ZeroDivisionError, IndexError):
        return None


def image_to_base64(image_path, max_size=(220, 220)):
    """Convertit une image en base64 pour l'afficher dans le popup HTML."""
    try:
        with Image.open(image_path) as img:
            img = img.copy()
            img.thumbnail(max_size)

            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{encoded}"
    except Exception:
        return None


def extract_metadata(image_path):
    """
    Extracts EXIF from a single image and builds a comprehensive data dictionary.
    """
    path = Path(image_path)

    safe_filename = sanitize_to_ascii(path.name)
    if not safe_filename or safe_filename.startswith('.'):
        safe_filename = f"image_id_{path.stem.encode('utf-8').hex()[:8]}{path.suffix}"

    face_data = detect_faces_in_image(image_path)

    try:
        with Image.open(image_path) as img:
            exif = img.getexif()
            if not exif:
                raise ValueError("No EXIF found")

            full_data = {}

            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                full_data[tag] = value

            gps_ifd = exif.get_ifd(0x8825)
            for tag_id, value in gps_ifd.items():
                tag = GPSTAGS.get(tag_id, tag_id)
                full_data[tag] = value

            exif_ifd = exif.get_ifd(0x8769)
            for tag_id, value in exif_ifd.items():
                tag = TAGS.get(tag_id, tag_id)
                full_data[tag] = value
            print("FACES:", safe_filename, face_data["faces_count"], len(face_data["face_signatures"]))

            return {
                "filename": safe_filename,
                "datetime": datatime(full_data),
                "latitude": latitude(full_data),
                "longitude": longitude(full_data),
                "camera_make": camera_make(full_data),
                "camera_model": camera_model(full_data),
                "has_gps": has_gps(full_data),
                "image_base64": image_to_base64(image_path),
                "has_faces": face_data["has_faces"],
                "faces_count": face_data["faces_count"],
                "faces_boxes": face_data["faces_boxes"],
                "face_signatures": face_data["face_signatures"],
            }

    except Exception:
        print("FACES:", safe_filename, face_data["faces_count"], len(face_data["face_signatures"]))
        return {
            "filename": safe_filename,
            "datetime": None,
            "latitude": None,
            "longitude": None,
            "camera_make": None,
            "camera_model": None,
            "has_gps": False,
            "image_base64": image_to_base64(image_path),
            "has_faces": face_data["has_faces"],
            "faces_count": face_data["faces_count"],
            "faces_boxes": face_data["faces_boxes"],
            "face_signatures": face_data["face_signatures"],

        }



def extract_all(folder_path):
    """Extracts metadata from all JPG files in a folder."""

    all_metadata = []
    folder = Path(folder_path)

    if not folder.is_dir():
        return []

    for path in folder.glob("*"):
        if path.is_file() and path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            metadata = extract_metadata(path)
            all_metadata.append(metadata)

    return all_metadata
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_BASE_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "images"))
GENERATED_REPORTS_DIR = os.path.join(BASE_DIR, "generated_reports")
ALLOWED_PROJECT_FOLDERS = {
    "ready": os.path.join(IMAGES_BASE_DIR, "ready"),
    "sample_data": os.path.join(IMAGES_BASE_DIR, "sample_data"),
    "uploads": os.path.join(IMAGES_BASE_DIR, "uploads"),
    "all": IMAGES_BASE_DIR,
}


@app.route("/")
def index():
    return render_template("index.html")


def _collect_project_images(project_folder: str):
    images_data = []

    if project_folder == "all":
        for folder_name in ["ready", "sample_data", "uploads"]:
            folder_path = ALLOWED_PROJECT_FOLDERS[folder_name]
            if os.path.isdir(folder_path):
                images_data.extend(extract_all(folder_path))
        return images_data

    folder_path = ALLOWED_PROJECT_FOLDERS.get(project_folder)
    if not folder_path or not os.path.isdir(folder_path):
        raise ValueError("תיקיית פרויקט לא נמצאה")

    return extract_all(folder_path)


def _collect_uploaded_images(photos):
    if not photos or all(photo.filename == "" for photo in photos):
        raise ValueError("לא נבחרו תמונות")

    with tempfile.TemporaryDirectory() as temp_dir:
        for photo in photos:
            if photo and photo.filename:
                save_path = os.path.join(temp_dir, photo.filename)
                photo.save(save_path)

        return extract_all(temp_dir)


def _load_images_from_request():
    source_type = request.form.get("source_type", "project")

    if source_type == "project":
        project_folder = request.form.get("project_folder", "ready")
        return _collect_project_images(project_folder)

    photos = request.files.getlist("photos")
    return _collect_uploaded_images(photos)


def _build_analysis_payload(images_data):
    map_html = create_map(images_data)
    timeline_html = create_timeline(images_data)
    analysis = analyze(images_data)
    report_html = create_report(images_data, map_html, timeline_html, analysis)
    return {
        "map_html": map_html,
        "timeline_html": timeline_html,
        "analysis": analysis,
        "report_html": report_html,
    }


def _is_valid_email(email):
    if not email:
        return False
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None


@app.route("/analyze", methods=["POST"])
def analyze_images():
    try:
        images_data = _load_images_from_request()
    except ValueError as exc:
        return str(exc), 400

    if not images_data:
        return "לא נמצאו תמונות תקינות", 400

    payload = _build_analysis_payload(images_data)
    return payload["report_html"]


@app.route("/export-pdf", methods=["POST"])
def export_pdf():
    try:
        images_data = _load_images_from_request()
    except ValueError as exc:
        return str(exc), 400

    if not images_data:
        return "לא נמצאו תמונות תקינות", 400

    payload = _build_analysis_payload(images_data)

    os.makedirs(GENERATED_REPORTS_DIR, exist_ok=True)
    pdf_path = os.path.join(GENERATED_REPORTS_DIR, "image_intel_report.pdf")

    export_report_to_pdf(images_data, payload["analysis"], pdf_path)

    return send_file(pdf_path, as_attachment=True, download_name="image_intel_report.pdf")


@app.route("/send-email", methods=["POST"])
def send_email():
    recipient_email = request.form.get("recipient_email", "").strip()

    if not _is_valid_email(recipient_email):
        return "כתובת מייל לא תקינה", 400

    try:
        images_data = _load_images_from_request()
    except ValueError as exc:
        return str(exc), 400

    if not images_data:
        return "לא נמצאו תמונות תקינות", 400

    payload = _build_analysis_payload(images_data)

    os.makedirs(GENERATED_REPORTS_DIR, exist_ok=True)
    pdf_path = os.path.join(GENERATED_REPORTS_DIR, "image_intel_report.pdf")

    export_report_to_pdf(images_data, payload["analysis"], pdf_path)

    try:
        send_pdf_email(recipient_email, pdf_path)
    except Exception as exc:
        return f"שגיאה בשליחת המייל: {str(exc)}", 500

    return f"""
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>שליחת מייל</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #0f172a;
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }}
            .box {{
                background: #1e293b;
                padding: 30px;
                border-radius: 18px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 500px;
            }}
            a {{
                color: #38bdf8;
                text-decoration: none;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="box">
            <h2>✅ הדו״ח נשלח בהצלחה</h2>
            <p>קובץ ה-PDF נשלח לכתובת:</p>
            <p><strong>{recipient_email}</strong></p>
            <p><a href="/">חזרה לדף הראשי</a></p>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(debug=True)