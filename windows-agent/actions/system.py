"""
Jack AI Windows Agent — System Control
Volume, brightness, power, media controls.
"""
import subprocess
import time
from loguru import logger

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False
    logger.warning("pycaw not available - using fallback volume control")

try:
    import screen_brightness_control as sbc
    SBC_AVAILABLE = True
except ImportError:
    SBC_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


class SystemController:

    # ── Volume ──────────────────────────────────────────────────────────────────
    def set_volume(self, params: dict) -> dict:
        """Set system volume (0-100) or increase/decrease."""
        level = params.get("level")
        action = params.get("action", "").lower()

        try:
            if PYCAW_AVAILABLE:
                return self._set_volume_pycaw(level, action)
            else:
                return self._set_volume_powershell(level, action)
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _set_volume_pycaw(self, level, action):
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        current = volume.GetMasterVolumeLevelScalar() * 100

        if action == "increase":
            new_level = min(100, current + 15)
        elif action == "decrease":
            new_level = max(0, current - 15)
        elif action == "mute":
            volume.SetMute(1, None)
            return {"success": True, "message": "Volume mute ho gaya"}
        elif action == "unmute":
            volume.SetMute(0, None)
            return {"success": True, "message": "Volume unmute ho gaya"}
        else:
            new_level = float(level) if level is not None else current

        volume.SetMasterVolumeLevelScalar(new_level / 100, None)
        logger.success(f"✅ Volume: {new_level:.0f}%")
        return {"success": True, "message": f"Volume {new_level:.0f}% ho gaya"}

    def _set_volume_powershell(self, level, action):
        if action in ("mute", "unmute"):
            script = f"(New-Object -ComObject WScript.Shell).SendKeys([char]173)"
            subprocess.run(["powershell", "-c", script])
            return {"success": True, "message": f"Volume {action} ho gaya"}

        if level is not None:
            script = f"""
$volume = {int(level)}
$wshShell = New-Object -ComObject wscript.shell
$currentVol = [math]::Round($volume * 0.65535)
"""
            subprocess.run(["powershell", "-c", script])

        return {"success": True, "message": "Volume set ho gaya"}

    # ── Brightness ──────────────────────────────────────────────────────────────
    def set_brightness(self, params: dict) -> dict:
        level = params.get("level")
        action = params.get("action", "").lower()

        if not SBC_AVAILABLE:
            return {"success": False, "message": "screen-brightness-control install nahi hai"}

        try:
            current = sbc.get_brightness(display=0)[0]

            if action == "increase":
                new_level = min(100, current + 15)
            elif action == "decrease":
                new_level = max(10, current - 15)
            else:
                new_level = float(level) if level is not None else current

            sbc.set_brightness(int(new_level), display=0)
            logger.success(f"✅ Brightness: {new_level:.0f}%")
            return {"success": True, "message": f"Brightness {new_level:.0f}% ho gayi"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── Power ───────────────────────────────────────────────────────────────────
    def shutdown(self, params: dict) -> dict:
        delay = params.get("delay", 5)
        logger.warning(f"⚠️  {delay} seconds mein shutdown ho raha hai!")
        subprocess.run(["shutdown", "/s", "/t", str(delay)])
        return {"success": True, "message": f"Computer {delay} seconds mein band ho raha hai"}

    def restart(self, params: dict) -> dict:
        delay = params.get("delay", 5)
        logger.warning(f"⚠️  {delay} seconds mein restart ho raha hai!")
        subprocess.run(["shutdown", "/r", "/t", str(delay)])
        return {"success": True, "message": f"Computer {delay} seconds mein restart ho raha hai"}

    def sleep(self, params: dict) -> dict:
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
        return {"success": True, "message": "Computer sleep ho raha hai"}

    # ── Media ───────────────────────────────────────────────────────────────────
    def _media_key(self, key_code: int):
        """Send a media key using PowerShell."""
        if PYAUTOGUI_AVAILABLE:
            key_map = {
                179: "playpause",
                176: "nexttrack",
                177: "prevtrack",
                178: "stop",
            }
            pyautogui.press(key_map.get(key_code, "playpause"))
        else:
            script = f"(New-Object -ComObject WScript.Shell).SendKeys([char]{key_code})"
            subprocess.run(["powershell", "-c", script])

    def media_play(self, params: dict) -> dict:
        self._media_key(179)  # Play/Pause
        return {"success": True, "message": "Media play ho gaya"}

    def media_pause(self, params: dict) -> dict:
        self._media_key(179)  # Play/Pause toggle
        return {"success": True, "message": "Media pause ho gaya"}

    def media_next(self, params: dict) -> dict:
        self._media_key(176)  # Next track
        return {"success": True, "message": "Agla track chal raha hai"}

    def media_prev(self, params: dict) -> dict:
        self._media_key(177)  # Previous track
        return {"success": True, "message": "Pichla track chal raha hai"}
