from datetime import datetime


def _parse_datetime(dt_str):
    if not dt_str:
        return None

    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue

    return None


def create_timeline(images_data):
    """
    יוצר ציר זמן ויזואלי של התמונות.

    Args:
        images_data: רשימת מילונים מ-extract_all

    Returns:
        string של HTML (ציר הזמן כ-HTML)
    """
    valid_images = [img for img in images_data if _parse_datetime(img.get("datetime")) is not None]

    if not valid_images:
        return """
        <div style="padding:20px; border:1px solid #ccc; border-radius:8px;">
            <h3>No timeline data available</h3>
            <p>No images with valid datetime were found.</p>
        </div>
        """

    valid_images.sort(key=lambda img: _parse_datetime(img.get("datetime")))

    items_html = []
    for img in valid_images:
        camera = f'{img.get("camera_make") or "Unknown"} {img.get("camera_model") or "Unknown"}'.strip()
        location = (
            f'{img.get("latitude")}, {img.get("longitude")}'
            if img.get("latitude") is not None and img.get("longitude") is not None
            else "No GPS"
        )

        items_html.append(f"""
        <div style="
            position: relative;
            margin: 20px 0 20px 30px;
            padding: 15px;
            border-left: 3px solid #2563eb;
            background: #f8fafc;
            border-radius: 8px;
        ">
            <div style="
                position: absolute;
                left: -10px;
                top: 18px;
                width: 14px;
                height: 14px;
                background: #2563eb;
                border-radius: 50%;
            "></div>
            <h4 style="margin: 0 0 8px 0;">{img.get("filename")}</h4>
            <p style="margin: 4px 0;"><b>Datetime:</b> {img.get("datetime")}</p>
            <p style="margin: 4px 0;"><b>Camera:</b> {camera}</p>
            <p style="margin: 4px 0;"><b>Location:</b> {location}</p>
        </div>
        """)

    return f"""
    <div style="padding: 20px;">
        <h3>Timeline</h3>
        {''.join(items_html)}
    </div>
    """