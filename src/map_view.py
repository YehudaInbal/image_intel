import folium
from datetime import datetime


def sort_by_time(arr):
    def parse_dt(item):
        dt = item.get("datetime")
        if not dt:
            return datetime.max
        try:
            return datetime.strptime(dt, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return datetime.max

    return sorted(arr, key=parse_dt)


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
        return """
        <div style="padding:20px; border:1px solid #ccc; border-radius:8px;">
            <h3>No GPS data available</h3>
            <p>No images with GPS coordinates were found.</p>
        </div>
        """

    gps_images = sort_by_time(gps_images)

    avg_lat = sum(img["latitude"] for img in gps_images) / len(gps_images)
    avg_lon = sum(img["longitude"] for img in gps_images) / len(gps_images)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=8)

    colors = [
        "red", "blue", "green", "purple", "orange",
        "darkred", "lightred", "beige", "darkblue", "darkgreen"
    ]

    device_colors = {}
    color_index = 0

    points = []

    for img in gps_images:
        device_name = f'{img.get("camera_make") or "Unknown"} {img.get("camera_model") or "Unknown"}'.strip()

        if device_name not in device_colors:
            device_colors[device_name] = colors[color_index % len(colors)]
            color_index += 1

        marker_color = device_colors[device_name]

        popup_text = f"""
        <b>Filename:</b> {img.get('filename')}<br>
        <b>Datetime:</b> {img.get('datetime')}<br>
        <b>Camera:</b> {device_name}
        """

        folium.Marker(
            location=[img["latitude"], img["longitude"]],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=img.get("filename"),
            icon=folium.Icon(color=marker_color)
        ).add_to(m)

        points.append((img["latitude"], img["longitude"]))

    if len(points) > 1:
        folium.PolyLine(points, color="blue", weight=3, opacity=0.7).add_to(m)

    legend_items = "".join(
        f'<li><span style="color:{color}; font-weight:bold;">●</span> {device}</li>'
        for device, color in device_colors.items()
    )

    legend_html = f"""
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        z-index: 9999;
        background-color: white;
        padding: 10px;
        border: 2px solid grey;
        border-radius: 8px;
        font-size: 14px;
        ">
        <b>Devices</b>
        <ul style="margin: 5px 0 0 15px; padding: 0;">
            {legend_items}
        </ul>
    </div>
    """

    m.get_root().html.add_child(folium.Element(legend_html))

    return m._repr_html_()