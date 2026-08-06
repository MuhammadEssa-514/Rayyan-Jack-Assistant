"""
Jack AI Voice Engine Configuration
"""
import os
from pathlib import Path
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# ─── Server ───────────────────────────────────────────────────────────────────
SERVER_URL = os.getenv("JACK_SERVER_URL", "http://localhost:5000")

# ─── Wake Word ────────────────────────────────────────────────────────────────
WAKE_WORD = os.getenv("WAKE_WORD", "hey_jarvis")  # OpenWakeWord model name
# Options: hey_jarvis, alexa, hey_mycroft, hey_rhasspy
# "Jack" custom model can be trained later with OpenWakeWord
WAKE_WORD_THRESHOLD = float(os.getenv("WAKE_WORD_THRESHOLD", "0.5"))
WAKE_WORD_SENSITIVITY = float(os.getenv("WAKE_WORD_SENSITIVITY", "0.7"))

# ─── Speech Recognition ───────────────────────────────────────────────────────
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
# Options: tiny, base, small (recommended), medium, large-v3
# small = best balance of speed + accuracy for Urdu
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", None)  # None = auto-detect
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "auto")    # auto, cpu, cuda
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")  # int8 = fastest on CPU

# ─── Audio ────────────────────────────────────────────────────────────────────
SAMPLE_RATE = 16000          # Hz - required by Whisper
CHUNK_SIZE = 1280            # samples per chunk (80ms at 16kHz)
LISTEN_TIMEOUT = 8           # seconds to wait after wake word
MIN_SILENCE_DURATION = 0.8   # seconds of silence to stop recording
AUDIO_CHANNELS = 1           # mono
MIC_INDEX = None             # None = default mic

# ─── TTS ──────────────────────────────────────────────────────────────────────
TTS_ENABLED = os.getenv("TTS_ENABLED", "true").lower() == "true"
# Piper TTS model for Urdu (download from piper releases)
# If Urdu model not available, use English model
PIPER_MODEL = os.getenv("PIPER_MODEL", str(MODELS_DIR / "ur_PK-usman-medium.onnx"))
PIPER_CONFIG = os.getenv("PIPER_CONFIG", str(MODELS_DIR / "ur_PK-usman-medium.onnx.json"))
# Fallback English model
PIPER_MODEL_EN = os.getenv("PIPER_MODEL_EN", str(MODELS_DIR / "en_US-lessac-medium.onnx"))

# ─── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = str(BASE_DIR / "logs" / "voice-engine.log")
