import os
import webbrowser
import threading
import subprocess
import sys
import importlib


def ensure_packages():
    """
    Vérifie si les packages nécessaires sont installés.
    Sinon les installe automatiquement avec pip.
    """

    required_packages = {
        "flask": "flask",
        "PIL": "Pillow",
        "piexif": "piexif",
        "folium": "folium",
        "matplotlib": "matplotlib",
        "pytest": "pytest",
        "reportlab": "reportlab",
        "cv2": "opencv-python",      # Face detection
        "branca": "branca",          # requis par folium

    }

    for module, package in required_packages.items():
        try:
            importlib.import_module(module)

        except ImportError:
            print(f"[INFO] Installing missing package: {package}")

            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                package
            ])


# installation automatique
ensure_packages()


# ajoute src au path Python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


from app import app


def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    print("Starting Image Intel...")
    print("Verification des dependances...")

    threading.Timer(1.5, open_browser).start()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )