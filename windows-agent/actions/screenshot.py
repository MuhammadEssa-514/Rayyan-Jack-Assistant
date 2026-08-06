"""
Jack AI Windows Agent — Screenshot Module
"""
import os
import time
from datetime import datetime
from loguru import logger
import config

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ScreenshotController:

    def __init__(self):
        os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)

    def take(self, params: dict) -> dict:
        """Take a screenshot and save it."""
        filename = params.get("filename") or f"jack_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(config.SCREENSHOT_DIR, filename)

        try:
            if MSS_AVAILABLE:
                with mss.mss() as sct:
                    monitor = sct.monitors[0]  # Full screen
                    img = sct.grab(monitor)
                    mss.tools.to_png(img.rgb, img.size, output=filepath)
            else:
                import pyautogui
                img = pyautogui.screenshot()
                img.save(filepath)

            logger.success(f"✅ Screenshot: {filepath}")
            return {
                "success": True,
                "message": f"Screenshot le liya",
                "data": {"filepath": filepath, "filename": filename},
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
