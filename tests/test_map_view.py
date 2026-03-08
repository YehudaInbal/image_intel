from src.map_view import sort_by_time, create_map


def test_sort_by_time():
    data = [
        {"filename": "b.jpg", "datetime": "2025-01-13 09:00:00"},
        {"filename": "a.jpg", "datetime": "2025-01-12 08:30:00"},
    ]
    result = sort_by_time(data)
    assert result[0]["filename"] == "a.jpg"
    assert result[1]["filename"] == "b.jpg"


def test_create_map_returns_html():
    fake_data = [
        {
            "filename": "test1.jpg",
            "datetime": "2025-01-12 08:30:00",
            "latitude": 32.0853,
            "longitude": 34.7818,
            "camera_make": "Samsung",
            "camera_model": "Galaxy S23",
            "has_gps": True,
        },
        {
            "filename": "test2.jpg",
            "datetime": "2025-01-13 09:00:00",
            "latitude": 31.7683,
            "longitude": 35.2137,
            "camera_make": "Apple",
            "camera_model": "iPhone 15 Pro",
            "has_gps": True,
        },
    ]

    html = create_map(fake_data)

    assert isinstance(html, str)
    assert "iframe" in html or "folium" in html.lower()


def test_create_map_no_gps():
    fake_data = [
        {
            "filename": "test3.jpg",
            "datetime": None,
            "latitude": None,
            "longitude": None,
            "camera_make": None,
            "camera_model": None,
            "has_gps": False,
        }
    ]

    html = create_map(fake_data)

    assert isinstance(html, str)
    assert "No GPS data available" in html