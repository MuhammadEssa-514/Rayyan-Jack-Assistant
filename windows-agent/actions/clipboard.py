"""
Jack AI Windows Agent — Clipboard Control
"""
from loguru import logger

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


class ClipboardController:

    def copy(self, params: dict) -> dict:
        """Copy text to clipboard."""
        text = params.get("text", "")
        if text and PYPERCLIP_AVAILABLE:
            pyperclip.copy(text)
            return {"success": True, "message": "Copy ho gaya"}
        elif PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey("ctrl", "c")
            return {"success": True, "message": "Copy ho gaya"}
        return {"success": False, "message": "Clipboard access nahi ho saka"}

    def paste(self, params: dict) -> dict:
        """Paste from clipboard."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey("ctrl", "v")
            return {"success": True, "message": "Paste ho gaya"}
        return {"success": False, "message": "Paste nahi ho saka"}

    def get_content(self, params: dict) -> dict:
        """Get current clipboard text."""
        if PYPERCLIP_AVAILABLE:
            text = pyperclip.paste()
            return {"success": True, "data": text, "message": "Clipboard content mila"}
        return {"success": False, "message": "Clipboard read nahi ho saka"}
