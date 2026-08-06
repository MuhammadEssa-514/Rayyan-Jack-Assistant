"""
Jack AI Windows Agent Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Server connection
SERVER_URL = os.getenv("JACK_SERVER_URL", "http://localhost:5000")
DEVICE_ID = os.getenv("WINDOWS_DEVICE_ID", "windows-main")
DEVICE_NAME = os.getenv("WINDOWS_DEVICE_NAME", "Windows Laptop")

# Browser settings
DEFAULT_BROWSER = os.getenv("DEFAULT_BROWSER", "chrome")  # chrome, firefox, edge

# Automation settings
ACTION_DELAY = float(os.getenv("ACTION_DELAY", "0.1"))   # seconds between actions
SCREENSHOT_DIR = os.getenv("SCREENSHOT_DIR", "./screenshots")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Tesseract OCR path (installed by UB-Mannheim installer)
TESSERACT_PATH = os.getenv(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
