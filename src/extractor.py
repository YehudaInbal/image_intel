from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from pathlib import Path


def has_gps(data: dict):
    gps_info = data.get("GPSInfo")
    return gps_info is not None


def _convert_to_degrees(value):
    """
    Convert GPS coordinates stored as EXIF rational tuples to float degrees.
    """
    if not value:
        return None

    def to_float(x):
        # PIL may return tuples like (num, den) or IFDRational-like objects
        try:
            return float(x)
        except Exception:
            return float(x[0]) / float(x[1])

    degrees = to_float(value[0])
    minutes = to_float(value[1])
    seconds = to_float(value[2])

    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def _get_gps_data(data: dict):
    gps_info = data.get("GPSInfo")
    if not gps_info:
        return None

    gps_data = {}
    for key, value in gps_info.items():
        decoded = GPSTAGS.get(key, key)
        gps_data[decoded] = value
    return gps_data


def latitude(data: dict):
    gps_data = _get_gps_data(data)
    if not gps_data:
        return None

    lat = gps_data.get("GPSLatitude")
    lat_ref = gps_data.get("GPSLatitudeRef")

    if not lat or not lat_ref:
        return None

    lat_value = _convert_to_degrees(lat)
    if lat_value is None:
        return None

    if lat_ref in ["S", b"S"]:
        lat_value = -lat_value

    return round(lat_value, 6)


def longitude(data: dict):
    gps_data = _get_gps_data(data)
    if not gps_data:
        return None

    lon = gps_data.get("GPSLongitude")
    lon_ref = gps_data.get("GPSLongitudeRef")

    if not lon or not lon_ref:
        return None

    lon_value = _convert_to_degrees(lon)
    if lon_value is None:
        return None

    if lon_ref in ["W", b"W"]:
        lon_value = -lon_value

    return round(lon_value, 6)


def datatime(data: dict):
    # keeping the original function name to match the existing call
    return data.get("DateTimeOriginal") or data.get("DateTime") or None


def camera_make(data: dict):
    return data.get("Make")


def camera_model(data: dict):
    return data.get("Model")


def extract_metadata(image_path):
    """
    שולף EXIF מתמונה בודדת.

    Args:
        image_path: נתיב לקובץ תמונה

    Returns:
        dict עם: filename, datetime, latitude, longitude,
              camera_make, camera_model, has_gps
    """
    path = Path(image_path)

    try:
        img = Image.open(image_path)
        exif = img._getexif()
    except Exception:
        exif = None

    if exif is None:
        return {
            "filename": path.name,
            "datetime": None,
            "latitude": None,
            "longitude": None,
            "camera_make": None,
            "camera_model": None,
            "has_gps": False
        }

    data = {}
    for tag_id, value in exif.items():
        tag = TAGS.get(tag_id, tag_id)
        data[tag] = value

    lat = latitude(data)
    lon = longitude(data)

    exif_dict = {
        "filename": path.name,
        "datetime": datatime(data),
        "latitude": lat,
        "longitude": lon,
        "camera_make": camera_make(data),
        "camera_model": camera_model(data),
        "has_gps": lat is not None and lon is not None
    }
    return exif_dict


def extract_all(folder_path):
    """
    שולף EXIF מכל התמונות בתיקייה.

    Args:
        folder_path: נתיב לתיקייה

    Returns:
        list של dicts (כמו extract_metadata)
    """
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        return []

    allowed_suffixes = {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"}

    results = []
    for file_path in sorted(folder.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() in allowed_suffixes:
            results.append(extract_metadata(file_path))

    return results