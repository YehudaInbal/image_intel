"""
timeline.py - יצירת ציר זמן ויזואלי
צוות 2, זוג A

מקבל רשימת תמונות ומחזיר HTML string של ציר זמן כרונולוגי.
"""

from datetime import datetime


def _parse_datetime(dt_str):
    """Parse plusieurs formats de dates possibles."""
    if not dt_str:
        return None

    formats = [
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y:%m:%d",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue

    return None


def _format_display_date(dt_obj, original_value):
    if dt_obj is None:
        return original_value or "—"
    return dt_obj.strftime("%d/%m/%Y • %H:%M")


def create_timeline(images_data):
    """
    יוצר ציר זמן HTML כרונולוגי של התמונות.

    Args:
        images_data: רשימת מילונים מ-extract_all

    Returns:
        HTML string
    """
    if not images_data:
        return """
        <div class="timeline-empty">
            אין נתוני תמונות להצגה בציר הזמן.
        </div>
        """

    dated_images = []
    for img in images_data:
        raw_dt = img.get("datetime")
        parsed_dt = _parse_datetime(raw_dt)
        if parsed_dt is not None:
            enriched = dict(img)
            enriched["_parsed_datetime"] = parsed_dt
            dated_images.append(enriched)

    if not dated_images:
        return """
        <div class="timeline-empty">
            לא נמצאו תמונות עם תאריך תקין, ולכן לא ניתן להציג ציר זמן.
        </div>
        """

    dated_images.sort(key=lambda x: x["_parsed_datetime"])

    items_html = ""
    previous_dt = None

    for i, img in enumerate(dated_images, start=1):
        dt_obj = img["_parsed_datetime"]
        display_dt = _format_display_date(dt_obj, img.get("datetime"))
        filename = img.get("filename", "—")
        camera = img.get("camera_model") or img.get("camera_make") or "Unknown"
        has_gps = "כן" if img.get("has_gps") else "לא"

        gap_html = ""
        if previous_dt is not None:
            gap = dt_obj - previous_dt
            hours = int(gap.total_seconds() // 3600)
            if hours >= 12:
                gap_html = f"""
                <div class="timeline-gap">
                    פער זמן גדול: {hours} שעות
                </div>
                """
        image_html = ""
        if img.get("image_base64"):
            image_html = f"""
            <div class="timeline-image-wrap">
                <img class="timeline-image" src="{img['image_base64']}" alt="{filename}">
            </div>
            """

        items_html += f"""
        {gap_html}
        <div class="timeline-item">
            <div class="timeline-marker">
                <div class="timeline-number">{i}</div>
            </div>
            <div class="timeline-content">
                <div class="timeline-date">{display_dt}</div>
                <div class="timeline-file">📷 {filename}</div>
                {image_html}
                <div class="timeline-meta"><span>מכשיר:</span> {camera}</div>
                <div class="timeline-meta"><span>GPS:</span> {has_gps}</div>
            </div>
        </div>
        """

        previous_dt = dt_obj

    return f"""
    <style>
    
        
        
        .timeline-root {{
            max-width: 760px;
            margin: 0 auto;
            position: relative;
            padding: 8px 0;
        }}

        .timeline-root::before {{
            content: "";
            position: absolute;
            top: 0;
            bottom: 0;
            right: 22px;
            width: 4px;
            background: linear-gradient(180deg, #2e86ab 0%, #1b4f72 100%);
            border-radius: 999px;
        }}

        .timeline-item {{
            position: relative;
            display: flex;
            align-items: flex-start;
            gap: 18px;
            padding: 0 0 18px 0;
        }}

        .timeline-marker {{
            position: relative;
            z-index: 2;
            width: 48px;
            min-width: 48px;
            display: flex;
            justify-content: center;
        }}

        .timeline-number {{
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: #2e86ab;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            font-weight: 800;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.14);
            border: 3px solid white;
        }}

        .timeline-content {{
            flex: 1;
            background: linear-gradient(180deg, #ffffff 0%, #f9fbfe 100%);
            border: 1px solid #d9e3ee;
            border-radius: 14px;
            padding: 14px 16px;
            box-shadow: 0 6px 18px rgba(13, 27, 42, 0.07);
        }}

        .timeline-date {{
            font-size: 0.95rem;
            font-weight: 800;
            color: #1b4f72;
            margin-bottom: 8px;
        }}

        .timeline-file {{
            font-size: 1rem;
            font-weight: 800;
            color: #0d1b2a;
            margin-bottom: 8px;
            word-break: break-word;
        }}

        .timeline-meta {{
            font-size: 0.92rem;
            color: #4b5d73;
            margin-top: 4px;
        }}

        .timeline-meta span {{
            font-weight: 800;
            color: #1b4f72;
        }}

        .timeline-gap {{
            margin: 4px 48px 16px 0;
            background: #fff5e8;
            color: #9b5c00;
            border: 1px solid #f3d19b;
            border-radius: 999px;
            padding: 7px 12px;
            font-size: 0.82rem;
            font-weight: 800;
            width: fit-content;
        }}

        .timeline-empty {{
            text-align: center;
            color: #6b7a8d;
            background: #f8fbfe;
            border: 1px dashed #d0dce9;
            border-radius: 12px;
            padding: 20px;
        }}

        @media (max-width: 640px) {{
            .timeline-root {{
                max-width: 100%;
            }}

            .timeline-content {{
                padding: 12px 13px;
            }}

            .timeline-file {{
                font-size: 0.95rem;
            }}
            
            .timeline-image-wrap {{
                margin: 10px 0 8px;
            }}
            
            .timeline-image {{
                display: block;
                width: 100%;
                max-width: 220px;
                height: auto;
                border-radius: 10px;
                border: 1px solid #d9e3ee;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            }}
        }}
    </style>

    <div class="timeline-root">
        {items_html}
    </div>
    """


if __name__ == "__main__":
    fake_data = [
        {
            "filename": "IMG_2889.JPG",
            "datetime": "2018:07:26 15:41:38",
            "camera_make": "Apple",
            "camera_model": "iPhone 6",
            "has_gps": True,
        },
        {
            "filename": "IMG_2925.JPG",
            "datetime": "2018:07:29 20:59:12",
            "camera_make": "Apple",
            "camera_model": "iPhone 6",
            "has_gps": True,
        },
        {
            "filename": "IMG_3042.JPG",
            "datetime": "2018:08:05 17:26:34",
            "camera_make": "Apple",
            "camera_model": "iPhone 6",
            "has_gps": True,
        },
    ]

    html = create_timeline(fake_data)

    with open("test_timeline.html", "w", encoding="utf-8") as f:
        f.write(f"""
        <!DOCTYPE html>
        <html lang="he" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>Timeline Test</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #f4f7fb;
                    margin: 0;
                    padding: 30px;
                }}
                .wrapper {{
                    max-width: 900px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 16px;
                    padding: 24px;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
                }}
            </style>
        </head>
        <body>
            <div class="wrapper">
                <h1>ציר זמן</h1>
                {html}
            </div>
        </body>
        </html>
        """)

    print("test_timeline.html saved")