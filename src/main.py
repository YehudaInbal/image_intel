import os
import sys
import webbrowser
import threading

# ajoute src au path Python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from app import app


def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    print("Image Intel démarre...")
    # threading.Timer(1.5, open_browser).start()
    # app.run(debug=True, host="127.0.0.1", port=5000)
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.5, open_browser).start()

    app.run(debug=True, host="127.0.0.1", port=5000)