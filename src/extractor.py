from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from pathlib import Path
import re
import base64
import io

def sanitize_to_ascii(text):
    """
    Removes any non-ASCII characters (like Hebrew) from the string.
    This ensures the output contains only English letters, numbers, and symbols.
    """
    if not text:
        return text
    # This regex keeps standard printable ASCII characters and removes everything else
    return re.sub(r'[^\x20-\x7E]', '', text).strip()


def get_gps_dict(data: dict):
    """
    Extracts GPS-related tags from the general metadata dictionary.
    """
    gps_readable = {}
    for key, value in data.items():
        if key.startswith("GPS"):
            gps_readable[key] = value
    return gps_readable


def has_gps(data: dict):
    """Checks if both latitude and longitude exist in the data."""
    gps_readable = get_gps_dict(data)
    return "GPSLatitude" in gps_readable and "GPSLongitude" in gps_readable


def latitude(data: dict):
    """Extracts and converts latitude to decimal format."""
    gps_data = get_gps_dict(data)
    lat_values = gps_data.get("GPSLatitude")
    ref = gps_data.get("GPSLatitudeRef")

    if lat_values and ref:
        return dms_to_decimal(lat_values, ref)
    return None


def longitude(data: dict):
    """Extracts and converts longitude to decimal format."""
    gps_data = get_gps_dict(data)
    lon_values = gps_data.get("GPSLongitude")
    ref = gps_data.get("GPSLongitudeRef")

    if lon_values and ref:
        return dms_to_decimal(lon_values, ref)
    return None


def datatime(data: dict):
    """Searches for the original timestamp in the metadata."""
    dt = data.get("DateTimeOriginal") or data.get("DateTimeDigitized") or data.get("DateTime")
    if dt is not None:
        return str(dt).strip()
    return None


def camera_make(data: dict):
    """Extracts camera manufacturer."""
    make = data.get("Make")
    if make is not None:
        return str(make).strip('\x00').strip()
    return None


def camera_model(data: dict):
    """Extracts camera model name."""
    model = data.get("Model")
    if model is not None:
        return str(model).strip('\x00').strip()
    return None


def dms_to_decimal(dms_tuple, ref):
    """Converts Degrees/Minutes/Seconds tuple to decimal float."""
    try:
        degrees = float(dms_tuple[0])
        minutes = float(dms_tuple[1])
        seconds = float(dms_tuple[2])

        decimal = degrees + minutes / 60 + seconds / 3600
        if ref in [b'S', b'W', 'S', 'W']:
            decimal = -decimal
        return decimal
    except (TypeError, ZeroDivisionError, IndexError):
        return None

def image_to_base64(image_path, max_size=(220, 220)):
    """Convertit une image en base64 pour l'afficher dans le popup HTML."""
    try:
        with Image.open(image_path) as img:
            img = img.copy()
            img.thumbnail(max_size)

            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{encoded}"
    except Exception:
        return None


    
def extract_metadata(image_path):
    """
    Extracts EXIF from a single image and builds a comprehensive data dictionary.
    """
    path = Path(image_path)

    # Pre-sanitize the filename so it's ready for both Success and Error cases
    safe_filename = sanitize_to_ascii(path.name)
    if not safe_filename or safe_filename.startswith('.'):
        # Generate a fallback name if the original was Hebrew
        safe_filename = f"image_id_{path.stem.encode('utf-8').hex()[:8]}{path.suffix}"

    try:
        with Image.open(image_path) as img:
            exif = img.getexif()
            if not exif:
                raise ValueError("No EXIF found")
            full_data = {}
            # Root EXIF tags
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                full_data[tag] = value

            # GPS IFD tags
            gps_ifd = exif.get_ifd(0x8825)
            for tag_id, value in gps_ifd.items():
                tag = GPSTAGS.get(tag_id, tag_id)
                full_data[tag] = value

            # Extended EXIF IFD tags
            exif_ifd = exif.get_ifd(0x8769)
            for tag_id, value in exif_ifd.items():
                tag = TAGS.get(tag_id, tag_id)
                full_data[tag] = value

            return {
                "filename": safe_filename,
                "datetime": datatime(full_data),
                "latitude": latitude(full_data),
                "longitude": longitude(full_data),
                "camera_make": camera_make(full_data),
                "camera_model": camera_model(full_data),
                "has_gps": has_gps(full_data),
                "image_base64": image_to_base64(image_path)
            }

    except Exception:
        return {
            "filename": safe_filename,
            "datetime": None,
            "latitude": None,
            "longitude": None,
            "camera_make": None,
            "camera_model": None,
            "has_gps": False,
            "image_base64": image_to_base64(image_path)
        }




def extract_all(folder_path):
    """Extracts metadata from all JPG files in a folder."""
    all_metadata = []
    folder = Path(folder_path)

    if not folder.is_dir():
        return []

    for path in folder.glob("*"):
        if path.is_file() and path.suffix.lower() in ['.jpg', '.jpeg','.png']:
            metadata = extract_metadata(path)
            all_metadata.append(metadata)

    return all_metadata