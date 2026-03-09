
# from timeline import create_timeline
# from analyzer import analyze
# from report import create_report
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


def fake_analyze(images_data):
    unique_cameras = set()
    gps_count = 0

    for img in images_data:
        if img.get("has_gps"):
            gps_count += 1

        device = img.get("camera_model") or img.get("camera_make")
        if device:
            unique_cameras.add(device)

    return {
        "total_images": len(images_data),
        "images_with_gps": gps_count,
        "unique_cameras": list(unique_cameras),
        "insights": [
            "הדו\"ח כרגע רץ עם analyzer זמני.",
            f"נמצאו {gps_count} תמונות עם GPS.",
            f"זוהו {len(unique_cameras)} מכשירים שונים."
        ]
    }


def fake_create_report(images_data, map_html, timeline_html, analysis):
    insights_html = "".join(f"<li>{insight}</li>" for insight in analysis.get("insights", []))
    cameras_html = "".join(
        f"<span style='display:inline-block; background:#2E86AB; color:white; padding:6px 10px; border-radius:14px; margin:4px;'>{cam}</span>"
        for cam in analysis.get("unique_cameras", [])
    )

    safe_map_html = (
        map_html
        .replace("&", "&amp;")
        .replace("'", "&apos;")
    )

    return f"""
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>Image Intel Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .header {{
                background: #1B4F72;
                color: white;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
            }}
            .section {{
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .stats {{
                display: flex;
                gap: 20px;
                justify-content: center;
                flex-wrap: wrap;
            }}
            .stat-card {{
                background: #E8F4FD;
                padding: 15px 25px;
                border-radius: 8px;
                text-align: center;
                min-width: 140px;
            }}
            .stat-number {{
                font-size: 2em;
                font-weight: bold;
                color: #1B4F72;
            }}
            .map-frame {{
                width: 100%;
                height: 520px;
                border: none;
                border-radius: 8px;
                background: white;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Image Intel Report</h1>
            <p>דו\"ח מודיעין חזותי</p>
        </div>

        <div class="section">
            <h2>סיכום</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{analysis.get("total_images", 0)}</div>
                    <div>תמונות</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{analysis.get("images_with_gps", 0)}</div>
                    <div>עם GPS</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(analysis.get("unique_cameras", []))}</div>
                    <div>מכשירים</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>תובנות</h2>
            <ul>{insights_html}</ul>
        </div>

        <div class="section">
            <h2>מפה</h2>
            <iframe class="map-frame" srcdoc='{safe_map_html}'></iframe>
        </div>

        <div class="section">
            <h2>ציר זמן</h2>
            {timeline_html}
        </div>

        <div class="section">
            <h2>מכשירים</h2>
            {cameras_html}
        </div>
    </body>
    </html>
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
        analysis = fake_analyze(images_data)
        report_html = fake_create_report(images_data, map_html, timeline_html, analysis)

        # map_html = create_map(images_data)
        # timeline_html = create_timeline(images_data)
        # analysis = analyze(images_data)
        # report_html = create_report(images_data, map_html, timeline_html, analysis)
        return report_html


if __name__ == "__main__":
    app.run(debug=True)