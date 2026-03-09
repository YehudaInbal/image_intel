"""
map_view.py - יצירת מפה אינטראקטיבית
צוות 1, זוג B

ראו docs/api_contract.md לפורמט הקלט והפלט.

=== תיקונים ===
1. חישוב מרכז המפה - היה עובר על images_data (כולל תמונות בלי GPS) במקום gps_image, נופל עם None
2. הסרת CustomIcon שלא עובד (filename זה לא נתיב שהדפדפן מכיר)
3. הסרת m.save() - לפי API contract צריך להחזיר HTML string, לא לשמור קובץ
4. הסרת fake_data מגוף הקובץ - הועבר ל-if __name__
5. תיקון color_index - היה מתקדם על כל תמונה במקום רק על מכשיר חדש
6. הוספת מקרא מכשירים
"""


import folium
import webbrowser
import os
from extractor import extract_all

def sort_by_time(arr):
    return sorted(arr, key=lambda x: (x.get("datetime") is None, x.get("datetime")))


def create_map(images_data):
    """
    יוצר מפה אינטראקטיבית עם כל המיקומים.

    Args:
        images_data: רשימת מילונים מ-extract_all

    Returns:
        string של HTML (המפה)
    """
    gps_images = [
        img for img in images_data
        if img.get("has_gps") and img.get("latitude") is not None and img.get("longitude") is not None
    ]

    if not gps_images:
        m = folium.Map(location=[32.0853, 34.7818], zoom_start=7)
        return m.get_root().render()

    gps_images = sort_by_time(gps_images)

    avg_lat = sum(img["latitude"] for img in gps_images) / len(gps_images)
    avg_lon = sum(img["longitude"] for img in gps_images) / len(gps_images)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=10)

    colors = ["red", "green", "blue", "purple", "orange", "darkred", "cadetblue"]
    device_colors = {}
    color_index = 0

    points = []

    for i, img in enumerate(gps_images, start=1):
        device = img.get("camera_model") or img.get("camera_make") or "Unknown"

        if device not in device_colors:
            device_colors[device] = colors[color_index % len(colors)]
            color_index += 1

        marker_color = device_colors[device]

        lat = img["latitude"]
        lon = img["longitude"]
        points.append([lat, lon])

        popup_html = f"""
        <div style="font-family: sans-serif; width: 220px;">
            <h4 style="margin: 0 0 10px 0;">📷 {img.get("filename", "Unknown")}</h4>
            <p style="margin: 5px 0;"><b>Photo #:</b> {i}</p>
            <p style="margin: 5px 0;"><b>Time:</b> {img.get("datetime", "Unknown")}</p>
            <p style="margin: 5px 0;"><b>Device:</b> {device}</p>
            <p style="margin: 5px 0;">
                <b>Coordinates:</b><br>
                {lat:.6f}, {lon:.6f}
            </p>
        </div>
        """

        popup = folium.Popup(popup_html, max_width=250)
        tooltip_text = f"{device} - {img.get('datetime', 'Unknown')}"

        folium.Marker(
            location=[lat, lon],
            popup=popup,
            tooltip=tooltip_text,
            icon=folium.Icon(color=marker_color, icon="camera", prefix="fa"),
        ).add_to(m)

    if len(points) > 1:
        folium.PolyLine(
            points,
            color="blue",
            weight=3,
            opacity=0.6,
            tooltip="מסלול כרונולוגי"
        ).add_to(m)

    return m.get_root().render()


if __name__ == "__main__":
    data = extract_all("../images")

    html = create_map(data)

    file_name = "test_map.html"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Map saved to {file_name}")

    full_path = os.path.abspath(file_name)
    webbrowser.open(f"file://{full_path}")


