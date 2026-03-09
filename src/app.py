
# from timeline import create_timeline
from analyzer import analyze
from report import create_report
from flask import Flask, render_template, request
import os
import tempfile

from extractor import extract_all
from map_view import create_map

app = Flask(__name__)


def fake_create_timeline(images_data):
    return """
    <div style="padding: 20px; background: white; border-radius: 8px;">
        <h3>Timeline placeholder</h3>
        <p>המודול של ציר הזמן עדיין בבנייה.</p>
    </div>
    """








@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_images():
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
            return "לא נמצאו תמונות תקינות"
        if not any(img.get("has_gps") for img in images_data):
            print("Warning: no GPS found")


        map_html = create_map(images_data)
        timeline_html = fake_create_timeline(images_data)


        # map_html = create_map(images_data)
        # timeline_html = create_timeline(images_data)
        analysis = analyze(images_data)
        report_html = create_report(images_data, map_html, timeline_html, analysis)
        return report_html


if __name__ == "__main__":
    app.run(debug=True)