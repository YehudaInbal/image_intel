from src.analyzer import analyze


def test_analyze_basic_output():
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

    result = analyze(fake_data)

    assert result["total_images"] == 3
    assert result["images_with_gps"] == 2
    assert "Samsung Galaxy S23" in result["unique_cameras"]
    assert "Apple iPhone 15 Pro" in result["unique_cameras"]
    assert isinstance(result["insights"], list)


def test_analyze_date_range():
    fake_data = [
        {
            "filename": "a.jpg",
            "datetime": "2025-01-12 08:30:00",
            "latitude": None,
            "longitude": None,
            "camera_make": "Samsung",
            "camera_model": "Galaxy S23",
            "has_gps": False,
        },
        {
            "filename": "b.jpg",
            "datetime": "2025-01-15 09:00:00",
            "latitude": None,
            "longitude": None,
            "camera_make": "Samsung",
            "camera_model": "Galaxy S23",
            "has_gps": False,
        },
    ]

    result = analyze(fake_data)

    assert result["date_range"]["start"] == "2025-01-12"
    assert result["date_range"]["end"] == "2025-01-15"