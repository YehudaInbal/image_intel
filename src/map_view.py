# """
# map_view.py - יצירת מפה אינטראקטיבית
# צוות 1, זוג B
#
# ראו docs/api_contract.md לפורמט הקלט והפלט.
#
# === תיקונים ===
# 1. חישוב מרכז המפה - היה עובר על images_data (כולל תמונות בלי GPS) במקום gps_image, נופל עם None
# 2. הסרת CustomIcon שלא עובד (filename זה לא נתיב שהדפדפן מכיר)
# 3. הסרת m.save() - לפי API contract צריך להחזיר HTML string, לא לשמור קובץ
# 4. הסרת fake_data מגוף הקובץ - הועבר ל-if __name__
# 5. תיקון color_index - היה מתקדם על כל תמונה במקום רק על מכשיר חדש
# 6. הוספת מקרא מכשירים
# """
#
# from src.extractor import extract_all
# from branca.element import Element
# import folium
#
#
# def sort_by_time(arr):
#     return sorted(arr, key=lambda x: (x.get("datetime") is None, x.get("datetime")))
#
#
# def create_map(images_data):
#     """
#     יוצר מפה אינטראקטיבית עם כל המיקומים.
#
#     Args:
#         images_data: רשימת מילונים מ-extract_all
#
#     Returns:
#         string של HTML (המפה)
#     """
#     gps_images = [
#         img for img in images_data
#         if img.get("has_gps") and img.get("latitude") is not None and img.get("longitude") is not None
#     ]
#
#     if not gps_images:
#         m = folium.Map(location=[32.0853, 34.7818], zoom_start=7)
#         return m.get_root().render()
#
#     gps_images = sort_by_time(gps_images)
#
#     avg_lat = sum(img["latitude"] for img in gps_images) / len(gps_images)
#     avg_lon = sum(img["longitude"] for img in gps_images) / len(gps_images)
#
#     m = folium.Map(location=[avg_lat, avg_lon], zoom_start=10)
#
#     colors = ["red", "green", "blue", "purple", "orange", "darkred", "cadetblue"]
#     device_colors = {}
#     color_index = 0
#
#     points = []
#     cluster_counts = {}
#     cluster_exact_coords = {}
#
#     for i, img in enumerate(gps_images, start=1):
#         device = img.get("camera_model") or img.get("camera_make") or "Unknown"
#
#         if device not in device_colors:
#             device_colors[device] = colors[color_index % len(colors)]
#             color_index += 1
#
#         marker_color = device_colors[device]
#         lat = img["latitude"]
#         lon = img["longitude"]
#         points.append([lat, lon])
#
#         # --- Start of updated hover feature logic ---
#
#         # Create a compact HTML string for the hover tooltip (the small square)
#         # We use the base64 data already extracted by extractor.py
#         hover_tooltip_html = ""
#         if img.get("image_base64"):
#             hover_tooltip_html = f"""
#                 <div style="width: 140px; text-align: center; font-family: sans-serif; padding: 5px;">
#                     <img src="{img['image_base64']}"
#                          style="width: 100%; height: auto; border-radius: 4px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
#                     <div style="font-size: 11px; margin-top: 5px; font-weight: bold; color: #333;">
#                         {img.get("filename", "Unknown")}
#                     </div>
#                 </div>
#                 """
#         else:
#             # Fallback to simple text if image is missing
#             hover_tooltip_html = f"<strong>{img.get('filename')}</strong><br>{device}"
#
#         # Build the detailed popup HTML for when the user actually clicks the marker
#         image_popup_html = ""
#         if img.get("image_base64"):
#             image_popup_html = f"""
#                 <div style="margin-top:10px; text-align:center;">
#                     <img src="{img['image_base64']}"
#                          style="max-width:200px; max-height:200px; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.2);">
#                 </div>
#                 """
#
#         popup_html = f"""
#             <div style="font-family: sans-serif; width: 220px;">
#                 <h4 style="margin: 0 0 10px 0;">📷 {img.get("filename", "Unknown")}</h4>
#                 <p style="margin: 5px 0;"><b>Photo #:</b> {i}</p>
#                 <p style="margin: 5px 0;"><b>Time:</b> {img.get("datetime", "Unknown")}</p>
#                 <p style="margin: 5px 0;"><b>Device:</b> {device}</p>
#                 <p style="margin: 5px 0;"><b>Coordinates:</b><br>{lat:.6f}, {lon:.6f}</p>
#                 {image_popup_html}
#             </div>
#             """
#         # --- End of updated hover feature logic ---
#
#         popup = folium.Popup(popup_html, max_width=250)
#
#         # Apply the tooltip_html to show the image on hover
#         folium.Marker(
#             location=[lat, lon],
#             popup=popup,
#             tooltip=hover_tooltip_html,
#             icon=folium.Icon(color=marker_color, icon="camera", prefix="fa"),
#         ).add_to(m)
#
#     for cluster_key, count in cluster_counts.items():
#         if count >= 3:
#             cluster_points = [
#                 (img["latitude"], img["longitude"])
#                 for img in gps_images
#                 if (round(img["latitude"], 2), round(img["longitude"], 2)) == cluster_key
#             ]
#
#             center_lat = sum(lat for lat, lon in cluster_points) / len(cluster_points)
#             center_lon = sum(lon for lat, lon in cluster_points) / len(cluster_points)
#
#             folium.Circle(
#                 location=[center_lat, center_lon],
#                 radius=600,
#                 color="crimson",
#                 fill=True,
#                 fill_opacity=0.12,
#                 popup=f"ריכוז של {count} תמונות באזור {cluster_key[0]}, {cluster_key[1]}"
#             ).add_to(m)
#
#     focus_script = """
#     <script>
#     window.addEventListener("message", function(event) {
#
#         const data = event.data;
#         if (!data || data.type !== "focusMap") return;
#
#         const lat = data.lat;
#         const lon = data.lon;
#
#         if (typeof lat !== "number" || typeof lon !== "number") return;
#
#         // Find the leaflet map instance dynamically
#         let leafletMap = null;
#
#         for (let key in window) {
#             if (window[key] instanceof L.Map) {
#                 leafletMap = window[key];
#                 break;
#             }
#         }
#
#         if (!leafletMap) return;
#
#         leafletMap.flyTo([lat, lon], 15, {
#             animate: true,
#             duration: 1.5
#         });
#
#     });
#     </script>
#     """
#
#     m.get_root().html.add_child(Element(focus_script))
#     return m.get_root().render()
#
#
# if __name__ == "__main__":
#     data = extract_all("../images")
#     html = create_map(data)
#
#     with open("test_map.html", "w", encoding="utf-8") as f:
#         f.write(html)
#
#     print("Map saved to test_map.html")
#
#
#



"""
map_view.py - יצירת מפה אינטראקטיבית
צוות 1, זוג B
"""

from src.extractor import extract_all
from branca.element import Element
import folium
from folium import plugins  # נדרש עבור AntPath

def sort_by_time(arr):
    return sorted(arr, key=lambda x: (x.get("datetime") is None, x.get("datetime")))

def create_map(images_data):
    """
    יוצר מפה אינטראקטיבית עם מסלול מקווקו ונע.
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
        lat, lon = img["latitude"], img["longitude"]
        points.append([lat, lon])

        # Hover Tooltip Logic
        hover_tooltip_html = ""
        if img.get("image_base64"):
            hover_tooltip_html = f"""
                <div style="width: 140px; text-align: center; font-family: sans-serif; padding: 5px;">
                    <img src="{img['image_base64']}" style="width: 100%; height: auto; border-radius: 4px;">
                    <div style="font-size: 11px; margin-top: 5px; font-weight: bold;">{img.get("filename", "Unknown")}</div>
                </div>"""
        else:
            hover_tooltip_html = f"<strong>{img.get('filename')}</strong>"

        # Popup Logic
        popup_html = f"""
            <div style="font-family: sans-serif; width: 220px;">
                <h4 style="margin: 0;">📷 {img.get("filename", "Unknown")}</h4>
                <p><b>Time:</b> {img.get("datetime", "Unknown")}<br><b>Device:</b> {device}</p>
            </div>"""

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=hover_tooltip_html,
            icon=folium.Icon(color=marker_color, icon="camera", prefix="fa"),
        ).add_to(m)

    # --- הקוד החדש למסלול מקווקו וזז ---
    if len(points) > 1:
        plugins.AntPath(
            locations=points,
            dash_array=[10, 20],  # אורך הקווקוו
            delay=1000,           # מהירות התנועה (נמוך יותר = מהיר יותר)
            color="black",        # צבע הקו הראשי
            pulse_color="white",  # צבע ה"פעימה" שזזה
            weight=4,
            opacity=0.8,
            paused=False,
            reverse=False         # תנועה לפי סדר הנקודות (כרונולוגי)
        ).add_to(m)
    # -----------------------------------

    focus_script = """
    <script>
    window.addEventListener("message", function(event) {
        const data = event.data;
        if (!data || data.type !== "focusMap") return;
        let leafletMap = null;
        for (let key in window) {
            if (window[key] instanceof L.Map) { leafletMap = window[key]; break; }
        }
        if (leafletMap) leafletMap.flyTo([data.lat, data.lon], 15, {animate: true, duration: 1.5});
    });
    </script>"""
    m.get_root().html.add_child(Element(focus_script))
    return m.get_root().render()

if __name__ == "__main__":
    data = extract_all("../images")
    html = create_map(data)
    with open("test_map.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Map saved to test_map.html with animated path.")