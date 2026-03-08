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
        return m._repr_html_()

    gps_images = sort_by_time(gps_images)

    avg_lat = sum(img["latitude"] for img in gps_images) / len(gps_images)
    avg_lon = sum(img["longitude"] for img in gps_images) / len(gps_images)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=10)

    for img in gps_images:
        popup_text = (
            f"Filename: {img.get('filename', 'Unknown')}<br>"
            f"Camera: {img.get('camera_make', 'Unknown')} {img.get('camera_model', '')}<br>"
            f"Date: {img.get('datetime', 'Unknown')}"
        )

        folium.Marker(
            location=[img["latitude"], img["longitude"]],
            popup=popup_text
        ).add_to(m)

    return m._repr_html_()


if __name__ == "__main__":
    fake_data = [
        {
            "filename": "test1.jpg",
            "latitude": 32.0853,
            "longitude": 34.7818,
            "has_gps": True,
            "camera_make": "Samsung",
            "camera_model": "Galaxy S23",
            "datetime": "2025-01-12 08:30:00",
        },
        {
            "filename": "test2.jpg",
            "latitude": 31.7683,
            "longitude": 35.2137,
            "has_gps": True,
            "camera_make": "Apple",
            "camera_model": "iPhone 15 Pro",
            "datetime": "2025-01-13 09:00:00",
        },
    ]

    html = create_map(fake_data)
    with open("test_map.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Map saved to test_map.html")
