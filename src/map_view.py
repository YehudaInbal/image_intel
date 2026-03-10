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

from extractor import extract_all
from branca.element import Element
import folium


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
    cluster_counts = {}
    cluster_exact_coords = {}

    for i, img in enumerate(gps_images, start=1):
        device = img.get("camera_model") or img.get("camera_make") or "Unknown"

        if device not in device_colors:
            device_colors[device] = colors[color_index % len(colors)]
            color_index += 1

        marker_color = device_colors[device]

        lat = img["latitude"]
        lon = img["longitude"]
        points.append([lat, lon])
        cluster_key = (round(lat, 2), round(lon, 2))
        cluster_counts[cluster_key] = cluster_counts.get(cluster_key, 0) + 1

        if cluster_key not in cluster_exact_coords:
            cluster_exact_coords[cluster_key] = (lat, lon)

        image_html = ""
        if img.get("image_base64"):
            image_html = f"""
            <div style="margin-top:10px; text-align:center;">
                <img src="{img['image_base64']}"
                     style="max-width:200px; max-height:200px; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.2);">
            </div>
            """

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
            {image_html}
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

    map_name = m.get_name()
    for cluster_key, count in cluster_counts.items():
        if count >= 3:
            cluster_lat, cluster_lon = cluster_exact_coords[cluster_key]

            folium.Circle(
                location=[cluster_lat, cluster_lon],
                radius=600,  # rayon en mètres
                color="crimson",
                fill=True,
                fill_opacity=0.12,
                popup=f"ריכוז של {count} תמונות באזור {cluster_key[0]}, {cluster_key[1]}"
            ).add_to(m)

    focus_script = """
    <script>
    window.addEventListener("message", function(event) {

        const data = event.data;
        if (!data || data.type !== "focusMap") return;

        const lat = data.lat;
        const lon = data.lon;

        if (typeof lat !== "number" || typeof lon !== "number") return;

        // Find the leaflet map instance dynamically
        let leafletMap = null;

        for (let key in window) {
            if (window[key] instanceof L.Map) {
                leafletMap = window[key];
                break;
            }
        }

        if (!leafletMap) return;

        leafletMap.flyTo([lat, lon], 15, {
            animate: true,
            duration: 1.5
        });

    });
    </script>
    """

    m.get_root().html.add_child(Element(focus_script))

    return m.get_root().render()


if __name__ == "__main__":
    data = extract_all("../images")
    html = create_map(data)

    with open("test_map.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("Map saved to test_map.html")



