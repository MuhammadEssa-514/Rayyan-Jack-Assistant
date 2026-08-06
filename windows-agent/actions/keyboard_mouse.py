"""
Jack AI Windows Agent — Keyboard & Mouse Control
Type text, press keys, click, scroll.
"""
import time
from loguru import logger

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05  # 50ms between actions for stability
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.error("pyautogui not installed")

try:
    import keyboard as kb
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class KeyboardMouseController:

    def type_text(self, params: dict) -> dict:
        """Type text at current cursor position."""
        text = params.get("text", "")
        if not text:
            return {"success": False, "message": "Text den jo type karna hai"}

        if not PYAUTOGUI_AVAILABLE:
            return {"success": False, "message": "pyautogui install nahi hai"}

        try:
            # Use pyperclip paste method for better Unicode support (Urdu text)
            import pyperclip
            original = pyperclip.paste()
            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.1)
            pyperclip.copy(original)  # Restore clipboard
            logger.success(f"✅ Text type ho gaya: {text[:30]}...")
            return {"success": True, "message": "Text type ho gaya"}
        except ImportError:
            # Fallback: direct typing (may not work for Urdu)
            pyautogui.write(text, interval=0.02)
            return {"success": True, "message": "Text type ho gaya"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def press_keys(self, params: dict) -> dict:
        """Press keyboard shortcut."""
        keys = params.get("keys", [])
        key = params.get("key", "")

        if not PYAUTOGUI_AVAILABLE:
            return {"success": False, "message": "pyautogui install nahi hai"}

        try:
            if isinstance(keys, list) and len(keys) > 1:
                pyautogui.hotkey(*keys)
                combo = " + ".join(keys)
            elif isinstance(keys, list) and len(keys) == 1:
                pyautogui.press(keys[0])
                combo = keys[0]
            elif key:
                pyautogui.press(key)
                combo = key
            else:
                return {"success": False, "message": "Keys den"}

            logger.success(f"✅ Key pressed: {combo}")
            return {"success": True, "message": f"{combo} press ho gaya"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def click(self, params: dict) -> dict:
        """Click at coordinates or element."""
        x = params.get("x")
        y = params.get("y")
        button = params.get("button", "left")
        double = params.get("double", False)

        if not PYAUTOGUI_AVAILABLE:
            return {"success": False, "message": "pyautogui install nahi hai"}

        try:
            if x is not None and y is not None:
                if double:
                    pyautogui.doubleClick(x, y, button=button)
                else:
                    pyautogui.click(x, y, button=button)
                logger.success(f"✅ Click: ({x}, {y})")
                return {"success": True, "message": f"Click ho gaya ({x}, {y})"}
            else:
                # Click current position
                pyautogui.click(button=button)
                return {"success": True, "message": "Click ho gaya"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def scroll(self, params: dict) -> dict:
        """Scroll page."""
        direction = params.get("direction", "down")
        amount = int(params.get("amount", 3))

        if not PYAUTOGUI_AVAILABLE:
            return {"success": False, "message": "pyautogui install nahi hai"}

        try:
            scroll_amount = amount if direction == "up" else -amount
            pyautogui.scroll(scroll_amount)
            logger.success(f"✅ Scroll {direction} {amount}")
            return {"success": True, "message": f"Scroll {direction} ho gaya"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def move_mouse(self, params: dict) -> dict:
        """Move mouse to position."""
        x = params.get("x", 0)
        y = params.get("y", 0)
        duration = float(params.get("duration", 0.2))

        if not PYAUTOGUI_AVAILABLE:
            return {"success": False, "message": "pyautogui install nahi hai"}

        try:
            pyautogui.moveTo(x, y, duration=duration)
            return {"success": True, "message": f"Mouse ({x},{y}) par aa gaya"}
        except Exception as e:
            return {"success": False, "message": str(e)}
