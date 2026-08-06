"""
Jack AI Windows Agent — Application Control
Launch, close, and switch Windows applications.
"""
import subprocess
import os
import time
from loguru import logger

try:
    import pyautogui
    import psutil
    AUTOMATION_AVAILABLE = True
except ImportError:
    AUTOMATION_AVAILABLE = False

# Common app name → executable mapping
APP_MAP = {
    "chrome":        "chrome.exe",
    "google chrome": "chrome.exe",
    "firefox":       "firefox.exe",
    "mozilla":       "firefox.exe",
    "edge":          "msedge.exe",
    "microsoft edge":"msedge.exe",
    "notepad":       "notepad.exe",
    "calculator":    "calc.exe",
    "paint":         "mspaint.exe",
    "word":          "WINWORD.EXE",
    "excel":         "EXCEL.EXE",
    "powerpoint":    "POWERPNT.EXE",
    "outlook":       "OUTLOOK.EXE",
    "whatsapp":      "WhatsApp.exe",
    "telegram":      "Telegram.exe",
    "discord":       "Discord.exe",
    "spotify":       "Spotify.exe",
    "vlc":           "vlc.exe",
    "task manager":  "taskmgr.exe",
    "explorer":      "explorer.exe",
    "file explorer": "explorer.exe",
    "cmd":           "cmd.exe",
    "command prompt":"cmd.exe",
    "powershell":    "powershell.exe",
    "vs code":       "Code.exe",
    "vscode":        "Code.exe",
    "visual studio code": "Code.exe",
    "zoom":          "Zoom.exe",
    "teams":         "Teams.exe",
    "microsoft teams": "Teams.exe",
    "camera":        "microsoft.windows.camera:",  # Store app
    "settings":      "ms-settings:",
    "store":         "ms-windows-store:",
}


class AppController:

    def open_app(self, params: dict) -> dict:
        """Launch an application by name."""
        app_name = params.get("app_name", "").lower().strip()
        app_path = params.get("app_path", "")

        if not app_name and not app_path:
            return {"success": False, "message": "App ka naam den"}

        # Try custom path first
        if app_path and os.path.exists(app_path):
            return self._launch(app_path, app_name)

        # Look up in map
        exe = APP_MAP.get(app_name)

        if exe:
            # Handle Windows Store apps (ms-xxx: URIs)
            if exe.endswith(":"):
                return self._launch_uri(exe)
            return self._launch(exe, app_name)

        # Try searching PATH
        return self._launch(app_name, app_name)

    def _launch(self, exe: str, display_name: str = "") -> dict:
        """Launch executable."""
        try:
            subprocess.Popen(exe, shell=True)
            time.sleep(0.5)
            name = display_name or exe
            logger.success(f"✅ {name} khul gaya")
            return {"success": True, "message": f"{name} khul gaya", "appName": name}
        except Exception as e:
            logger.error(f"App launch error: {e}")
            return {"success": False, "message": f"{exe} nahi khul saka: {str(e)}"}

    def _launch_uri(self, uri: str) -> dict:
        """Launch a Windows URI (ms-settings:, etc.)."""
        try:
            os.startfile(uri)
            return {"success": True, "message": "App khul gaya"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def close_app(self, params: dict) -> dict:
        """Close a running application by name."""
        app_name = params.get("app_name", "").lower().strip()
        exe = APP_MAP.get(app_name, app_name)

        try:
            killed = False
            if AUTOMATION_AVAILABLE:
                for proc in psutil.process_iter(["name", "pid"]):
                    if proc.info["name"] and exe.lower() in proc.info["name"].lower():
                        proc.terminate()
                        killed = True
                        logger.success(f"✅ {app_name} band ho gaya")
            
            if not killed:
                # Fallback to taskkill command
                subprocess.run(f"taskkill /f /im {exe}*", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                killed = True

            return {"success": True, "message": f"{app_name} band ho gaya"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def open_folder(self, params: dict) -> dict:
        """Open a folder in File Explorer."""
        path = params.get("path", "")

        if not path:
            # Open Downloads by default
            path = os.path.expanduser("~/Downloads")

        # Expand common shortcuts
        replacements = {
            "downloads": os.path.expanduser("~/Downloads"),
            "desktop":   os.path.expanduser("~/Desktop"),
            "documents": os.path.expanduser("~/Documents"),
            "pictures":  os.path.expanduser("~/Pictures"),
            "music":     os.path.expanduser("~/Music"),
            "videos":    os.path.expanduser("~/Videos"),
        }

        path_lower = path.lower()
        for key, full_path in replacements.items():
            if key in path_lower:
                path = full_path
                break

        try:
            os.startfile(path)
            logger.success(f"✅ Folder khula: {path}")
            return {"success": True, "message": f"Folder khul gaya: {path}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
