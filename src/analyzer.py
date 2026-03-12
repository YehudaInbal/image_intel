import json
from extractor import extract_all

from pathlib import Path
from collections import Counter
from datetime import datetime

def coords_to_location_key(lat, lon, precision=2):
    """
    Converts coordinates into a simplified location key by rounding them.
    This replaces reverse geocoding and lets us detect revisits to roughly the same area.
    """
    if lat is None or lon is None:
        return None
    return round(lat, precision), round(lon, precision)


def get_date_range(dated_images):
    """Sorts images by timestamp and returns the start and end dates of the collection."""
    if not dated_images:
        return {"start": None, "end": None}

    dated_images.sort(key=lambda x: x["datetime"])
    return {"start": dated_images[0]["datetime"], "end": dated_images[-1]["datetime"]}


def analyze_behavior(dated_images):
    """Identifies behavioral patterns like night activity and high-volume upload days."""
    if not dated_images:
        return []

    behavior_insights = []

    hours = [int(img["datetime"].split()[1].split(":")[0]) for img in dated_images if " " in img["datetime"]]
    night_shots = len([h for h in hours if h < 6 or h > 22])
    if hours and night_shots > len(hours) * 0.5:
        behavior_insights.append("זוהה דפוס פעילות לילי: חלק משמעותי מהתמונות צולמו בשעות המאוחרות.")

    dates = [img["datetime"].split()[0] for img in dated_images]
    daily_counts = Counter(dates)
    busy_days = [date for date, count in daily_counts.items() if count > 5]
    if busy_days:
        behavior_insights.append(f"זוהו ימי פעילות אינטנסיביים (מעל 5 תמונות ליום): {', '.join(busy_days)}.")

    return behavior_insights


def get_device_insights(dated_images, unique_cameras):
    """Detects if the user switched hardware or uses multiple devices simultaneously."""
    insights = []

    if len(unique_cameras) > 1:
        insights.append(f"נמצאו {len(unique_cameras)} מכשירים שונים - ייתכן שהמשתמש החליף מכשיר.")

    for i in range(1, len(dated_images)):
        prev_cam = dated_images[i - 1].get("camera_model")
        curr_cam = dated_images[i].get("camera_model")
        if prev_cam and curr_cam and prev_cam != curr_cam:
            msg = f"בתאריך {dated_images[i]['datetime']}, המשתמש עבר מ-{prev_cam} ל-{curr_cam}."
            if msg not in insights:
                insights.append(msg)

    return insights


def detect_location_revisits(images_with_gps):
    """
    Traces movement patterns to identify if a user returned to a previously visited area.
    Uses rounded coordinates only for grouping, but keeps exact coordinates for map links.
    """
    if len(images_with_gps) < 3:
        return []

    sorted_imgs = sorted(images_with_gps, key=lambda x: x.get("datetime", ""))

    location_visits = []
    for img in sorted_imgs:
        lat = img.get("latitude")
        lon = img.get("longitude")
        location_key = coords_to_location_key(lat, lon, precision=2)

        if not location_key or lat is None or lon is None:
            continue

        if not location_visits or location_visits[-1]["location"] != location_key:
            location_visits.append({
                "location": location_key,   # coordonnées arrondies pour détecter le retour
                "lat": lat,                 # vraies coordonnées pour la map
                "lon": lon,                 # vraies coordonnées pour la map
                "datetime": img.get("datetime")
            })

    insights = []
    reported_locations = set()

    for i in range(len(location_visits) - 2):
        a1 = location_visits[i]
        b = location_visits[i + 1]
        a2 = location_visits[i + 2]

        if a1["location"] == a2["location"] and a1["location"] != b["location"]:
            if a1["location"] not in reported_locations:
                reported_locations.add(a1["location"])
                insights.append(
                    f'זוהתה חזרה לאזור '
                    f'<a href="#map-section" class="coord-link" data-lat="{a1["lat"]}" data-lon="{a1["lon"]}">'
                    f'{a1["lat"]:.6f}, {a1["lon"]:.6f}</a>: '
                    f'ביקור ראשון ב-{a1["datetime"]}, '
                    f'ביניים באזור '
                    f'<a href="#map-section" class="coord-link" data-lat="{b["lat"]}" data-lon="{b["lon"]}">'
                    f'{b["lat"]:.6f}, {b["lon"]:.6f}</a> '
                    f'({b["datetime"]}), '
                    f'חזרה ב-{a2["datetime"]}.'
                )

    return insights

def detect_time_gaps(dated_images, threshold_hours=12):
    """
    מזהה פערי זמן גדולים בין תמונות עוקבות.
    מחזיר רשימת תובנות בעברית.
    """
    if len(dated_images) < 2:
        return []

    insights = []

    sorted_images = sorted(dated_images, key=lambda x: x["datetime"])

    for i in range(1, len(sorted_images)):
        prev_dt_str = sorted_images[i - 1].get("datetime")
        curr_dt_str = sorted_images[i].get("datetime")

        if not prev_dt_str or not curr_dt_str:
            continue

        try:
            prev_dt = datetime.strptime(prev_dt_str, "%Y:%m:%d %H:%M:%S")
            curr_dt = datetime.strptime(curr_dt_str, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            try:
                prev_dt = datetime.strptime(prev_dt_str, "%Y-%m-%d %H:%M:%S")
                curr_dt = datetime.strptime(curr_dt_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

        gap = curr_dt - prev_dt
        gap_hours = int(gap.total_seconds() // 3600)

        if gap_hours >= threshold_hours:
            insights.append(
                f"זוהה פער זמן גדול של {gap_hours} שעות בין "
                f"{sorted_images[i - 1].get('filename', 'תמונה לא ידועה')} "
                f"לבין {sorted_images[i].get('filename', 'תמונה לא ידועה')}."
            )

    return insights

def detect_geographic_clusters(images_with_gps, precision=2, min_images=3):
    """
    מזהה ריכוזים גיאוגרפיים לפי קואורדינטות מקורבות.
    אם יש לפחות min_images תמונות באותו אזור - מחזיר תובנות עם קישור למפה.
    """
    if not images_with_gps:
        return []

    area_counts = Counter()
    area_coords = {}

    for img in images_with_gps:
        lat = img.get("latitude")
        lon = img.get("longitude")

        if lat is None or lon is None:
            continue

        area_key = (round(lat, precision), round(lon, precision))
        area_counts[area_key] += 1

        if area_key not in area_coords:
            area_coords[area_key] = (lat, lon)

    significant_clusters = []

    for area, count in area_counts.items():
        if count >= min_images:
            lat, lon = area_coords[area]
            significant_clusters.append({
                "area": area,
                "count": count,
                "lat": lat,
                "lon": lon
            })

    if not significant_clusters:
        return []

    significant_clusters.sort(key=lambda x: x["count"], reverse=True)

    insights = []

    # Insight détaillée pour chaque cluster
    for cluster in significant_clusters:
        insights.append(
            f'זוהה ריכוז גיאוגרפי של {cluster["count"]} תמונות באזור '
            f'<a href="#map-section" class="coord-link" '
            f'data-lat="{cluster["lat"]}" data-lon="{cluster["lon"]}">'
            f'{cluster["area"][0]}, {cluster["area"][1]}</a>.'
        )

    # Insight OSINT principale sur le cluster dominant
    top_cluster = significant_clusters[0]
    insights.append(
        f'זוהה מוקד פעילות מרכזי באזור '
        f'<a href="#map-section" class="coord-link" '
        f'data-lat="{top_cluster["lat"]}" data-lon="{top_cluster["lon"]}">'
        f'{top_cluster["area"][0]}, {top_cluster["area"][1]}</a> '
        f'עם {top_cluster["count"]} תמונות משויכות.'
    )

    return insights


def analyze(images_data):
    """Main entry point that runs all analysis modules and aggregates the findings."""
    if not images_data:
        return {
            "total_images": 0,
            "images_with_gps": 0,
            "images_with_datetime": 0,
            "unique_cameras": [],
            "date_range": {"start": None, "end": None},
            "insights": ["אין נתונים זמינים"]
        }

    images_with_gps = [img for img in images_data if img.get("has_gps")]
    dated_images = [img for img in images_data if img.get("datetime")]
    cameras = list(set([img.get("camera_model") for img in images_data if img.get("camera_model")]))

    date_range = get_date_range(dated_images)
    insights = get_device_insights(dated_images, cameras)
    insights.extend(analyze_behavior(dated_images))
    insights.extend(detect_time_gaps(dated_images))
    insights.extend(detect_geographic_clusters(images_with_gps))

    if images_with_gps:
        insights.append(f"מידע גיאוגרפי זמין עבור {len(images_with_gps)} תמונות. ניתן לבצע איכון.")
        insights.extend(detect_location_revisits(images_with_gps))

    return {
        "total_images": len(images_data),
        "images_with_gps": len(images_with_gps),
        "images_with_datetime": len(dated_images),
        "unique_cameras": cameras,
        "date_range": date_range,
        "insights": insights
    }


if __name__ == "__main__":
    folder_path = Path(r"C:\Users\bgdps\OneDrive\Documents\Final project\image_intel\images")

    if folder_path.exists():
        results = extract_all(folder_path) or []
        print("\n--- תוצאות ניתוח מודיעיני ---")
        print(json.dumps(analyze(results), indent=4, ensure_ascii=False))
    else:
        print(f"Error: Directory {folder_path} not found.")