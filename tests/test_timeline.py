from src.timeline import create_timeline


def test_create_timeline_returns_html():
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

    html = create_timeline(fake_data)

    assert isinstance(html, str)
    assert "Timeline" in html
    assert "test1.jpg" in html
    assert "test2.jpg" in html


def test_create_timeline_no_valid_dates():
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

    html = create_timeline(fake_data)

    assert isinstance(html, str)
    assert "No timeline data available" in html