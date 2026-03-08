import sys
from pathlib import Path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.append(str(project_root/"src"))
import extractor

folder_path_specific = Path(r"C:\Users\bgdps\OneDrive\Documents\Final project\image_intel\images\sample_data\20230118_070716.jpg")
folder_path = Path(r"C:\Users\bgdps\OneDrive\Documents\Final project\image_intel\images")
if folder_path.exists():
    print("The file is exist")
    results = extractor.extract_all(folder_path)
    for metadata in results:
        print(metadata)
else:
    print("The file is not exist in this folder")

# if folder_path_specific.exists():
#     print("The file is exist")
#     print(extractor.extract_metadata(folder_path_specific))
# else:
#     print("The file is not exist in this folder")