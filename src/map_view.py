"""
map_view.py - Create an interactive map
"""
from collections import Counter
from extractor import extract_all
from branca.element import Element
import folium
from folium import plugins


def sort_by_time(arr):
    return sorted(arr, key=lambda x: (x.get("datetime") is None, x.get("datetime")))


def create_map(images_data):
    """
    Creates an interactive map with:
    - Markers for each image
    - Moving dotted chronological track
    - Geographic hotspot detection
    - Heatmap of location density
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
    cluster_counts = Counter()
    cluster_coords = {}

    for i, img in enumerate(gps_images, start=1):
        device = img.get("camera_model") or img.get("camera_make") or "Unknown"

        if device not in device_colors:
            device_colors[device] = colors[color_index % len(colors)]
            color_index += 1

        marker_color = device_colors[device]
        lat, lon = img["latitude"], img["longitude"]
        points.append([lat, lon])

        cluster_key = (round(lat, 2), round(lon, 2))
        cluster_counts[cluster_key] += 1
        if cluster_key not in cluster_coords:
            cluster_coords[cluster_key] = (lat, lon)

        # Hover tooltip
        if img.get("image_base64"):
            hover_tooltip_html = f"""
                <div style="width: 140px; text-align: center; font-family: sans-serif; padding: 5px;">
                    <img src="{img['image_base64']}"
                         style="width: 100%; height: auto; border-radius: 4px; box-shadow: 0 2px 6px rgba(0,0,0,0.25);">
                    <div style="font-size: 11px; margin-top: 5px; font-weight: bold;">
                        {img.get("filename", "Unknown")}
                    </div>
                </div>
            """
        else:
            hover_tooltip_html = f"<strong>{img.get('filename', 'Unknown')}</strong>"

        # Popup
        image_popup_html = ""
        if img.get("image_base64"):
            image_popup_html = f"""
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
                <p style="margin: 5px 0;"><b>Coordinates:</b><br>{lat:.6f}, {lon:.6f}</p>
                {image_popup_html}
            </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=hover_tooltip_html,
            icon=folium.Icon(color=marker_color, icon="camera", prefix="fa"),
        ).add_to(m)

    # Animated chronological path
    if len(points) > 1:
        plugins.AntPath(
            locations=points,
            dash_array=[10, 20],
            delay=1000,
            color="black",
            pulse_color="white",
            weight=4,
            opacity=0.8,
            paused=False,
            reverse=False
        ).add_to(m)

    # Geographic hotspots
    for cluster_key, count in cluster_counts.items():
        if count >= 3:
            lat, lon = cluster_coords[cluster_key]

            folium.Circle(
                location=[lat, lon],
                radius=600,
                color="crimson",
                fill=True,
                fill_opacity=0.15,
                popup=f"""
                <b>Geographic Hotspot</b><br>
                {count} related images<br>
                {cluster_key[0]}, {cluster_key[1]}
                """
            ).add_to(m)

    # Heatmap
    heat_points = [[img["latitude"], img["longitude"]] for img in gps_images]
    if heat_points:
        plugins.HeatMap(
            heat_points,
            radius=25,
            blur=18,
            min_opacity=0.35
        ).add_to(m)

    # Focus script for report interactions
    focus_script = """
    <script>
    window.addEventListener("message", function(event) {
        const data = event.data;
        if (!data || data.type !== "focusMap") return;

        const lat = data.lat;
        const lon = data.lon;

        if (typeof lat !== "number" || typeof lon !== "number") return;

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

    print("Map saved to test_map.html with hotspots and heatmap.")