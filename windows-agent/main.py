"""
Jack AI Windows Agent — Main Entry Point
Connects to Jack AI server via Socket.IO and executes Windows commands.

Run: python main.py
"""
import sys
import time
import platform
import socket as net_socket
import signal
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", format="<cyan>{time:HH:mm:ss}</cyan> | <level>{level}</level> | {message}")

import config

# Import action modules
from actions.app_control import AppController
from actions.system import SystemController
from actions.keyboard_mouse import KeyboardMouseController
from actions.clipboard import ClipboardController
from actions.screenshot import ScreenshotController
from actions.browser import BrowserController
from actions.file_control import FileController

try:
    import socketio
    SIO_AVAILABLE = True
except ImportError:
    SIO_AVAILABLE = False
    logger.error("python-socketio not installed: pip install python-socketio[client] aiohttp")


class WindowsAgent:
    """
    Jack AI Windows Agent.
    Maintains persistent WebSocket connection to server and executes commands.
    """

    def __init__(self):
        self.running = False

        # Initialize action controllers
        self.app = AppController()
        self.system = SystemController()
        self.keyboard = KeyboardMouseController()
        self.clipboard = ClipboardController()
        self.screenshot = ScreenshotController()
        self.browser = BrowserController()
        self.file = FileController()

        # Intent → handler mapping
        self.handlers = {
            # App control
            "open_app":         self.app.open_app,
            "close_app":        self.app.close_app,

            # Browser
            "browse_url":       self.browser.open_url,
            "search_web":       self.browser.search,

            # Keyboard/Mouse
            "type_text":        self.keyboard.type_text,
            "press_key":        self.keyboard.press_keys,
            "click_element":    self.keyboard.click,
            "scroll":           self.keyboard.scroll,

            # System
            "set_volume":       self.system.set_volume,
            "set_brightness":   self.system.set_brightness,
            "shutdown":         self.system.shutdown,
            "restart":          self.system.restart,
            "sleep":            self.system.sleep,
            "play_music":       self.system.media_play,
            "pause_music":      self.system.media_pause,
            "next_track":       self.system.media_next,
            "prev_track":       self.system.media_prev,

            # Clipboard
            "copy_clipboard":   self.clipboard.copy,
            "paste_clipboard":  self.clipboard.paste,

            # Screenshot
            "screenshot":       self.screenshot.take,

            # Folder/File
            "open_folder":      self.app.open_folder,
            "create_file":      self.file.create_file,
            "delete_file":      self.file.delete_file,
        }

        # Setup Socket.IO
        self.sio = None
        self._setup_socketio()

    def _setup_socketio(self):
        if not SIO_AVAILABLE:
            return

        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,
            reconnection_delay=3,
            logger=False,
            engineio_logger=False,
        )

        @self.sio.event
        def connect():
            logger.success(f"🔌 Server se connected!")
            # Register this device
            self.sio.emit("register_device", {
                "type": "windows",
                "name": config.DEVICE_NAME,
                "deviceId": config.DEVICE_ID,
                "metadata": {
                    "os": "Windows",
                    "osVersion": platform.version(),
                    "hostname": net_socket.gethostname(),
                    "appVersion": "1.0.0",
                },
            })

        @self.sio.event
        def disconnect():
            logger.warning("⚠️  Server se disconnected")

        @self.sio.on("execute_command")
        def on_command(data):
            """Receive and execute a command from the server."""
            intent = data.get("intent", "unknown")
            params = data.get("parameters", {})
            logger.info(f"📥 Command mila: {intent} | params: {params}")

            result = self.execute(intent, params)

            # Send result back to server
            self.sio.emit("windows_result", {
                "commandId": data.get("commandId"),
                "intent": intent,
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "data": result.get("data"),
            })

        @self.sio.on("ping")
        def on_ping():
            self.sio.emit("heartbeat")

    def execute(self, intent: str, params: dict) -> dict:
        """Execute a command by intent name."""
        handler = self.handlers.get(intent)

        if not handler:
            logger.warning(f"⚠️  Unknown intent: {intent}")
            return {"success": False, "message": f"Intent '{intent}' pata nahi"}

        try:
            result = handler(params)
            return result or {"success": True, "message": "Kaam ho gaya"}
        except Exception as e:
            logger.error(f"❌ {intent} execute nahi hua: {e}")
            return {"success": False, "message": str(e)}

    def run(self):
        """Start agent and maintain connection."""
        if not self.sio:
            logger.error("Socket.IO available nahi hai")
            return

        self.running = True
        logger.info(f"🚀 Windows Agent shuru ho raha hai...")
        logger.info(f"🔌 Server: {config.SERVER_URL}")

        while self.running:
            try:
                if not self.sio.connected:
                    logger.info("Server se connect ho raha hoon...")
                    self.sio.connect(config.SERVER_URL)

                # Keep alive
                while self.running and self.sio.connected:
                    self.sio.emit("windows_event", {
                        "event": "status_update",
                        "payload": {"status": "online"},
                    })
                    time.sleep(30)

            except Exception as e:
                logger.error(f"Connection error: {e}")
                logger.info("5 seconds baad retry karoon ga...")
                time.sleep(5)

    def stop(self):
        self.running = False
        if self.sio and self.sio.connected:
            self.sio.disconnect()


def main():
    agent = WindowsAgent()

    def signal_handler(sig, frame):
        logger.info("Band ho raha hoon...")
        agent.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    agent.run()


if __name__ == "__main__":
    main()
