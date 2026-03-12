from pathlib import Path
import cv2
import math


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"

YUNET_PATH = str(MODEL_DIR / "face_detection_yunet_2023mar.onnx")
SFACE_PATH = str(MODEL_DIR / "face_recognition_sface_2021dec.onnx")

_face_detector = None
_face_recognizer = None


def _load_models():
    global _face_detector, _face_recognizer

    if _face_detector is not None and _face_recognizer is not None:
        return _face_detector, _face_recognizer

    if not Path(YUNET_PATH).exists():
        raise FileNotFoundError(f"Missing YuNet model: {YUNET_PATH}")

    if not Path(SFACE_PATH).exists():
        raise FileNotFoundError(f"Missing SFace model: {SFACE_PATH}")

    _face_detector = cv2.FaceDetectorYN.create(
        YUNET_PATH,
        "",
        (320, 320),
        score_threshold=0.88,
        nms_threshold=0.3,
        top_k=5000,
    )

    _face_recognizer = cv2.FaceRecognizerSF.create(
        SFACE_PATH,
        ""
    )

    return _face_detector, _face_recognizer


def _safe_face_box(face_row, img_w, img_h):
    x, y, w, h = face_row[:4]

    x = max(0, int(x))
    y = max(0, int(y))
    w = int(w)
    h = int(h)

    if w <= 0 or h <= 0:
        return None

    if x + w > img_w:
        w = img_w - x
    if y + h > img_h:
        h = img_h - y

    if w < 45 or h < 45:
        return None

    ratio = w / float(h)
    if ratio < 0.65 or ratio > 1.45:
        return None

    return x, y, w, h


def _extract_embedding(image, face_row, recognizer):
    try:
        aligned_face = recognizer.alignCrop(image, face_row)
        embedding = recognizer.feature(aligned_face)
        if embedding is None:
            return None
        return embedding.flatten().astype(float).tolist()
    except Exception:
        return None


def detect_faces_in_image(image_path):
    """
    Detect faces with YuNet and generate SFace embeddings.

    Returns:
        {
            "has_faces": bool,
            "faces_count": int,
            "faces_boxes": list[dict],
            "face_signatures": list[list[float]]
        }
    """
    try:
        image = cv2.imread(str(image_path))
        if image is None:
            return {
                "has_faces": False,
                "faces_count": 0,
                "faces_boxes": [],
                "face_signatures": []
            }

        detector, recognizer = _load_models()

        img_h, img_w = image.shape[:2]
        detector.setInputSize((img_w, img_h))

        _, faces = detector.detect(image)

        if faces is None or len(faces) == 0:
            return {
                "has_faces": False,
                "faces_count": 0,
                "faces_boxes": [],
                "face_signatures": []
            }

        boxes = []
        signatures = []

        for face_row in faces:
            safe_box = _safe_face_box(face_row, img_w, img_h)
            if safe_box is None:
                continue

            x, y, w, h = safe_box
            confidence = float(face_row[-1]) if len(face_row) >= 15 else 0.0

            boxes.append({
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "confidence": round(confidence, 3)
            })

            embedding = _extract_embedding(image, face_row, recognizer)
            if embedding is not None:
                signatures.append(embedding)

        return {
            "has_faces": len(boxes) > 0,
            "faces_count": len(boxes),
            "faces_boxes": boxes,
            "face_signatures": signatures
        }

    except Exception as e:
        print("FACE DETECTION ERROR:", e, flush=True)
        return {
            "has_faces": False,
            "faces_count": 0,
            "faces_boxes": [],
            "face_signatures": []
        }


def cosine_distance(sig1, sig2):
    if not sig1 or not sig2 or len(sig1) != len(sig2):
        return 1.0

    dot = sum(a * b for a, b in zip(sig1, sig2))
    norm1 = math.sqrt(sum(a * a for a in sig1))
    norm2 = math.sqrt(sum(b * b for b in sig2))

    if norm1 == 0 or norm2 == 0:
        return 1.0

    cosine_similarity = dot / (norm1 * norm2)
    return 1.0 - cosine_similarity


if __name__ == "__main__":
    try:
        detector, recognizer = _load_models()
        print("YUNET + SFACE MODELS LOADED OK")
        print("YUNET:", YUNET_PATH)
        print("SFACE:", SFACE_PATH)
        print("Detector ready.")
    except Exception as e:
        print("MODEL LOAD ERROR:")
        print(e)