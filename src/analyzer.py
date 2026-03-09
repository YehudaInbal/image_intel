from pathlib import Path
import extractor
def analyze(images_data):
    """
    מנתח את נתוני התמונות בהתאמה למבנה הנתונים של ה-extractor.
    """
    total_images = len(images_data)

    images_with_gps = len([img for img in images_data if img.get("has_gps") is True])

    dated_images = [img for img in images_data if img.get("datetime")]

    cameras = list(set([img.get("camera_model") for img in images_data if img.get("camera_model")]))

    sorted_images = []
    date_range = {"start": None, "end": None}

    if dated_images:
        sorted_images = sorted(dated_images, key=lambda x: x["datetime"])
        date_range["start"] = sorted_images[0]["datetime"]
        date_range["end"] = sorted_images[-1]["datetime"]

    insights = []

    if len(cameras) > 1:
        insights.append(f"נמצאו {len(cameras)} מכשירים שונים - ייתכן שהסוכן החליף מכשירים.")

    for i in range(1, len(sorted_images)):
        prev_cam = sorted_images[i - 1].get("camera_model")
        curr_cam = sorted_images[i].get("camera_model")
        if prev_cam and curr_cam and prev_cam != curr_cam:
            insights.append(f"בתאריך {sorted_images[i]['datetime']} הסוכן עבר מ-{prev_cam} ל-{curr_cam}.")

    if images_with_gps > 0:
        insights.append(f"קיימים נתוני מיקום עבור {images_with_gps} תמונות. ניתן לבצע איכון גיאוגרפי.")

    return {
        "total_images": total_images,
        "images_with_gps": images_with_gps,
        "images_with_datetime": len(dated_images),
        "unique_cameras": cameras,
        "date_range": date_range,
        "insights": insights
    }


if __name__ == "__main__":
    folder_path = Path(r"C:\Users\User\Desktop\python exercise\תרגולים\final_project\image_intel\images")
    if folder_path.exists():
        print("The file is exist")
        results = extractor.extract_all(folder_path)
    analysis_results = analyze(results)

    import json

    print(json.dumps(analysis_results, indent=4, ensure_ascii=False))