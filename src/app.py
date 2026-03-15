from flask import Flask, render_template, request, send_file
import os
import tempfile

from timeline import create_timeline
from analyzer import analyze
from report import create_report
from pdf_export import export_report_to_pdf
from extractor import extract_all
from map_view import create_map
from mail_sender import send_pdf_email
import re
import webbrowser
import threading

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

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    print("Starting Image Intel...")

    threading.Timer(1.5, open_browser).start()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000,
        use_reloader=False  # חשוב: מונע פתיחה כפולה של הדפדפן כשהשרת מתרענן
    )