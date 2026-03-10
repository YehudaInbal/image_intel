
from timeline import create_timeline
from analyzer import analyze
from report import create_report
from flask import Flask, render_template, request
import os
import tempfile

from extractor import extract_all
from map_view import create_map

app = Flask(__name__)



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_images():
    source_type = request.form.get("source_type", "project")

    if source_type == "project":
        project_folder = request.form.get("project_folder", "ready")

        allowed_folders = {
            "ready": "../images/ready",
            "sample_data": "../images/sample_data",
            "uploads": "../images/uploads",
        }

        folder_path = allowed_folders.get(project_folder)
        if not folder_path or not os.path.isdir(folder_path):
            return "תיקיית פרויקט לא נמצאה", 400

        images_data = extract_all(folder_path)

    else:
        photos = request.files.getlist("photos")

        if not photos or all(photo.filename == "" for photo in photos):
            return "לא נבחרו תמונות", 400

        with tempfile.TemporaryDirectory() as temp_dir:
            for photo in photos:
                if photo and photo.filename:
                    save_path = os.path.join(temp_dir, photo.filename)
                    photo.save(save_path)

            images_data = extract_all(temp_dir)

    if not images_data:
        return "לא נמצאו תמונות תקינות", 400

    map_html = create_map(images_data)
    timeline_html = create_timeline(images_data)
    analysis = analyze(images_data)
    report_html = create_report(images_data, map_html, timeline_html, analysis)

    return report_html


if __name__ == "__main__":
    app.run(debug=True)