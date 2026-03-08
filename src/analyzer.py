from datetime import datetime
from math import radians, sin, cos, sqrt, atan2


def _parse_datetime(dt_str):
    if not dt_str:
        return None

    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None


def _camera_name(img):
    make = img.get("camera_make") or ""
    model = img.get("camera_model") or ""
    name = f"{make} {model}".strip()
    return name if name else "Unknown"


def _haversine(lat1, lon1, lat2, lon2):
    r = 6371.0

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


def analyze(images_data):
    """
    מנתח את הנתונים ומוצא דפוסים.
    """
    total_images = len(images_data)
    gps_images = [
        img for img in images_data
        if img.get("has_gps") and img.get("latitude") is not None and img.get("longitude") is not None
    ]

    valid_dates = [img for img in images_data if _parse_datetime(img.get("datetime")) is not None]
    valid_dates_sorted = sorted(valid_dates, key=lambda img: _parse_datetime(img.get("datetime")))

    unique_cameras = sorted({_camera_name(img) for img in images_data if _camera_name(img) != "Unknown"})

    date_range = {"start": None, "end": None}
    if valid_dates_sorted:
        date_range["start"] = _parse_datetime(valid_dates_sorted[0]["datetime"]).strftime("%Y-%m-%d")
        date_range["end"] = _parse_datetime(valid_dates_sorted[-1]["datetime"]).strftime("%Y-%m-%d")

    insights = []

    if unique_cameras:
        insights.append(f"Found {len(unique_cameras)} unique camera(s)")

    if len(unique_cameras) > 1:
        insights.append("Multiple devices were used across the images")

    # detect camera switch over time
    for i in range(1, len(valid_dates_sorted)):
        prev_camera = _camera_name(valid_dates_sorted[i - 1])
        curr_camera = _camera_name(valid_dates_sorted[i])

        if prev_camera != curr_camera:
            date_str = _parse_datetime(valid_dates_sorted[i]["datetime"]).strftime("%Y-%m-%d")
            insights.append(f"Camera changed on {date_str}")
            break

    # detect significant time gaps
    for i in range(1, len(valid_dates_sorted)):
        prev_dt = _parse_datetime(valid_dates_sorted[i - 1]["datetime"])
        curr_dt = _parse_datetime(valid_dates_sorted[i]["datetime"])
        gap_hours = (curr_dt - prev_dt).total_seconds() / 3600

        if gap_hours >= 24:
            insights.append(f"Large time gap detected: {gap_hours:.1f} hours")
            break

    # detect long distance jumps
    gps_sorted = [img for img in valid_dates_sorted if img in gps_images]
    for i in range(1, len(gps_sorted)):
        prev = gps_sorted[i - 1]
        curr = gps_sorted[i]

        dist = _haversine(
            prev["latitude"], prev["longitude"],
            curr["latitude"], curr["longitude"]
        )

        if dist > 50:
            insights.append(f"Long-distance movement detected: {dist:.1f} km")
            break

    return {
        "total_images": total_images,
        "images_with_gps": len(gps_images),
        "unique_cameras": unique_cameras,
        "date_range": date_range,
        "insights": insights
    }