import json
from pathlib import Path
import extractor

def analyze(images_data):
    """
    Analyzes image metadata and extracts intelligence insights.
    """
    if not images_data:
        return {"error": "No data provided"}

    total_images = len(images_data)

    # Matching the key 'has_gps' from your extractor output
    images_with_gps = len([img for img in images_data if img.get("has_gps")])

    # Filter images that have a valid datetime string
    dated_images = [img for img in images_data if img.get("datetime")]

    # Extract unique camera models
    cameras = list(set([img.get("camera_model") for img in images_data if img.get("camera_model")]))

    # Calculate Date Range
    date_range = {"start": None, "end": None}
    if dated_images:
        # Sort by datetime to find the timeline
        dated_images.sort(key=lambda x: x["datetime"])
        date_range["start"] = dated_images[0]["datetime"]
        date_range["end"] = dated_images[-1]["datetime"]

    # Intelligence Insights Generation
    insights = []

    # Device Change Insight
    if len(cameras) > 1:
        insights.append(f"Found {len(cameras)} different devices - Potential device switching detected.")

    # Sequential Device Switching Timeline
    for i in range(1, len(dated_images)):
        prev_cam = dated_images[i - 1].get("camera_model")
        curr_cam = dated_images[i].get("camera_model")

        if prev_cam and curr_cam and prev_cam != curr_cam:
            change_msg = f"On {dated_images[i]['datetime']}, user switched from {prev_cam} to {curr_cam}."
            # Simple check to avoid redundant duplicate strings if many photos exist at once
            if change_msg not in insights:
                insights.append(change_msg)

    # GPS Availability Insight
    if images_with_gps > 0:
        insights.append(f"Location data available for {images_with_gps} images. Geolocation tracking is possible.")

    return {
        "total_images": total_images,
        "images_with_gps": images_with_gps,
        "images_with_datetime": len(dated_images),
        "unique_cameras": cameras,
        "date_range": date_range,
        "insights": insights
    }


if __name__ == "__main__":
    folder_path = Path(r"C:\Users\bgdps\OneDrive\Documents\Final project\image_intel\images")

    if folder_path.exists():
        print(f"Directory found: {folder_path}")

        # Extract data using your custom extractor
        results = extractor.extract_all(folder_path)

        # Run the analysis
        analysis_results = analyze(results)

        # Print final JSON output
        print("\n--- Intelligence Analysis Results ---")
        print(json.dumps(analysis_results, indent=4))
    else:
        print(f"Error: The directory {folder_path} does not exist.")


if __name__ == "__main__":
    folder_path = Path(r"C:\Users\bgdps\OneDrive\Documents\Final project\image_intel\images")
    if folder_path.exists():
        print("The file is exist")
        results = extractor.extract_all(folder_path)
    analysis_results = analyze(results)

    import json

    print(json.dumps(analysis_results, indent=4, ensure_ascii=False))