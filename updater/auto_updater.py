import requests
import webbrowser
from utils.logger import logger

CURRENT_VERSION = "1.0.0"
UPDATE_URL = "https://api.github.com/repos/yourusername/AegisBreach/releases/latest"  # placeholder

def check_for_updates():
    try:
        resp = requests.get(UPDATE_URL, timeout=5)
        if resp.status_code == 200:
            latest = resp.json()["tag_name"]
            if latest != CURRENT_VERSION:
                logger.info(f"New version available: {latest}")
                return True, latest
    except Exception as e:
        logger.warning(f"Update check failed: {e}")
    return False, CURRENT_VERSION

def open_download_page():
    webbrowser.open("https://github.com/yourusername/AegisBreach/releases")