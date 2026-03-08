from src.extractor import has_gps, latitude, longitude, datatime, camera_make, camera_model


def test_has_gps_true():
    data = {"GPSInfo": {1: "N", 2: ((32, 1), (5, 1), (0, 1))}}
    assert has_gps(data) is True


def test_has_gps_false():
    data = {}
    assert has_gps(data) is False


def test_latitude_positive():
    data = {
        "GPSInfo": {
            1: "N",
            2: ((32, 1), (30, 1), (0, 1)),
            3: "E",
            4: ((34, 1), (45, 1), (0, 1)),
        }
    }
    assert latitude(data) == 32.5


def test_longitude_positive():
    data = {
        "GPSInfo": {
            1: "N",
            2: ((32, 1), (30, 1), (0, 1)),
            3: "E",
            4: ((34, 1), (45, 1), (0, 1)),
        }
    }
    assert longitude(data) == 34.75


def test_latitude_negative_south():
    data = {
        "GPSInfo": {
            1: "S",
            2: ((10, 1), (0, 1), (0, 1)),
            3: "E",
            4: ((20, 1), (0, 1), (0, 1)),
        }
    }
    assert latitude(data) == -10.0


def test_longitude_negative_west():
    data = {
        "GPSInfo": {
            1: "N",
            2: ((10, 1), (0, 1), (0, 1)),
            3: "W",
            4: ((20, 1), (0, 1), (0, 1)),
        }
    }
    assert longitude(data) == -20.0


def test_datetime_original():
    data = {"DateTimeOriginal": "2025:01:12 08:30:00"}
    assert datatime(data) == "2025:01:12 08:30:00"


def test_camera_make():
    data = {"Make": "Samsung"}
    assert camera_make(data) == "Samsung"


def test_camera_model():
    data = {"Model": "Galaxy S23"}
    assert camera_model(data) == "Galaxy S23"