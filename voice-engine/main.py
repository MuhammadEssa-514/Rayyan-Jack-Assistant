"""
Jack AI Voice Engine — Main Entry Point
===================================================
Pipeline:
  Microphone → Wake Word → STT → Server (WebSocket) → TTS Response

Run: python main.py
"""
import asyncio
import signal
import sys
import time
import numpy as np
import queue
import threading
from loguru import logger
from pathlib import Path

# Setup logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")
logger.add("logs/voice-engine.log", rotation="10 MB", retention="7 days", level="DEBUG")

# Local modules
import config
from modules.wake_word import WakeWordDetector
from modules.speech_recognition import SpeechRecognizer
from modules.tts import TTSEngine

# SocketIO client
try:
    import socketio
    SIO_AVAILABLE = True
except ImportError:
    SIO_AVAILABLE = False
    logger.error("python-socketio not installed: pip install python-socketio[client] aiohttp")

import requests


class JackVoiceEngine:
    """
    Main voice engine controller.
    Manages the complete voice processing pipeline.
    """

    def __init__(self):
        self.running = False
        self.state = "idle"  # idle | listening | processing | speaking
        self.audio_queue = queue.Queue()

        # Initialize modules
        logger.info("🚀 Jack AI Voice Engine shuru ho raha hai...")

        self.wake_detector = WakeWordDetector(
            wake_word=config.WAKE_WORD,
            threshold=config.WAKE_WORD_THRESHOLD,
        )

        self.stt = SpeechRecognizer(
            model_size=config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
            language=config.WHISPER_LANGUAGE,
        )

        self.tts = TTSEngine(
            model_path=config.PIPER_MODEL,
            config_path=config.PIPER_CONFIG,
        )

        # Socket.IO client
        self.sio = None
        self._setup_socketio()

    def _setup_socketio(self):
        """Initialize Socket.IO connection to Jack AI server."""
        if not SIO_AVAILABLE:
            return

        self.sio = socketio.Client(reconnection=True, reconnection_attempts=0, reconnection_delay=2)

        @self.sio.event
        def connect():
            logger.success(f"🔌 Server se connected: {config.SERVER_URL}")
            self.sio.emit("register_device", {
                "type": "voice-engine",
                "name": "Jack Voice Engine",
                "deviceId": "voice-engine-main",
                "metadata": {"version": "1.0.0"},
            })

        @self.sio.event
        def disconnect():
            logger.warning("⚠️  Server se disconnected. Reconnect ho raha hai...")

        @self.sio.on("speak")
        def on_speak(data):
            """Server requests TTS playback."""
            text = data.get("text", "")
            if text:
                logger.info(f"🔊 TTS request: {text}")
                self.tts.speak(text, blocking=False)

        @self.sio.on("registered")
        def on_registered(data):
            logger.info(f"✅ Voice engine registered: {data}")

    def connect_server(self):
        """Connect to the Jack AI server."""
        if not self.sio:
            return False
        try:
            self.sio.connect(config.SERVER_URL, wait_timeout=5)
            return True
        except Exception as e:
            logger.warning(f"Server baat nahi kar raha ({e}). Offline mode mein chal raha hai.")
            return False

    def send_command(self, text: str):
        """Send transcribed text to server for AI processing."""
        # Try WebSocket first
        if self.sio and self.sio.connected:
            self.sio.emit("voice_command", {"text": text, "timestamp": time.time()})
            logger.debug(f"📤 Command via WebSocket bheja: {text}")
            return

        # Fallback to HTTP
        try:
            resp = requests.post(
                f"{config.SERVER_URL}/api/voice",
                json={"text": text},
                timeout=30,
            )
            data = resp.json()
            response_text = data.get("response_text", "")
            if response_text:
                self.tts.speak(response_text)
        except Exception as e:
            logger.error(f"HTTP command send error: {e}")

    def capture_audio_chunk(self, stream, chunk_size: int) -> np.ndarray:
        """Read one chunk of audio from the microphone stream."""
        try:
            data = stream.read(chunk_size, exception_on_overflow=False)
            return np.frombuffer(data, dtype=np.int16)
        except Exception as e:
            logger.error(f"Audio read error: {e}")
            return np.zeros(chunk_size, dtype=np.int16)

    def record_command(self, stream) -> np.ndarray:
        """
        Record audio until silence detected.
        Returns concatenated audio as float32 array.
        """
        logger.info("🎤 Bol rahe hain... (sunn raha hoon)")

        all_audio = []
        silence_frames = 0
        SILENCE_THRESHOLD = 300  # Amplitude threshold for silence
        MAX_SILENCE_FRAMES = int(config.MIN_SILENCE_DURATION * config.SAMPLE_RATE / config.CHUNK_SIZE)
        MAX_RECORD_FRAMES = int(config.LISTEN_TIMEOUT * config.SAMPLE_RATE / config.CHUNK_SIZE)

        frame_count = 0
        has_speech = False

        while frame_count < MAX_RECORD_FRAMES:
            chunk = self.capture_audio_chunk(stream, config.CHUNK_SIZE)
            all_audio.append(chunk)

            # Check amplitude for silence detection
            amplitude = np.abs(chunk).mean()

            if amplitude > SILENCE_THRESHOLD:
                has_speech = True
                silence_frames = 0
            else:
                silence_frames += 1

            # Stop if: speech detected + silence detected
            if has_speech and silence_frames >= MAX_SILENCE_FRAMES:
                break

            frame_count += 1

        if not all_audio:
            return np.array([], dtype=np.float32)

        # Concatenate and normalize
        audio_int16 = np.concatenate(all_audio)
        audio_float = audio_int16.astype(np.float32) / 32768.0
        return audio_float

    def run(self):
        """Main voice processing loop."""
        try:
            import pyaudio
        except ImportError:
            logger.error("pyaudio not installed: pip install pyaudio")
            return

        # Initialize models
        logger.info("🔄 Models load ho rahe hain...")
        self.wake_detector.initialize()
        self.stt.initialize()

        # Connect to server
        logger.info(f"🔌 Server se connect ho raha hai: {config.SERVER_URL}")
        self.connect_server()

        # Open microphone
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=config.AUDIO_CHANNELS,
            rate=config.SAMPLE_RATE,
            input=True,
            frames_per_buffer=config.CHUNK_SIZE,
            input_device_index=config.MIC_INDEX,
        )

        self.running = True
        logger.success("✅ Jack AI tayar hai! 'Jack' bol ke shuru karein...\n")
        self.tts.speak("Jack AI tayar hai. Bolo Jack aur apna command den.")

        try:
            while self.running:
                self.state = "idle"

                # ── Phase 1: Wait for wake word ──────────────────────────
                audio_chunk = self.capture_audio_chunk(stream, config.CHUNK_SIZE)
                
                if not self.wake_detector.detect(audio_chunk):
                    continue

                # ── Wake word detected! ──────────────────────────────────
                logger.success("🎯 WAKE WORD DETECTED! Sunn raha hoon...")
                self.state = "listening"

                # Notify server
                if self.sio and self.sio.connected:
                    self.sio.emit("voice_status", {"status": "listening"})

                # Play "ding" acknowledgment sound (optional)
                self.tts.speak("Haan?", blocking=False)

                # ── Phase 2: Record command ──────────────────────────────
                audio_data = self.record_command(stream)

                if len(audio_data) < config.SAMPLE_RATE * 0.5:
                    logger.info("Audio bahut chota hai, ignore kar raha hoon")
                    continue

                # ── Phase 3: Speech to Text ──────────────────────────────
                self.state = "processing"
                logger.info("🧠 Samajh raha hoon...")

                result = self.stt.transcribe(audio_data, config.SAMPLE_RATE)
                text = result["text"].strip()

                if not text:
                    logger.info("Kuch samajh nahi aaya, dobara try karein")
                    self.tts.speak("Maafi, kuch samajh nahi aaya. Dobara bolein?")
                    continue

                logger.success(f"📝 Suna: \"{text}\"")

                # ── Phase 4: Send to AI Brain via server ─────────────────
                self.send_command(text)

        except KeyboardInterrupt:
            logger.info("\n⏹️  Jack AI band ho raha hai...")
        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)
        finally:
            self.running = False
            stream.stop_stream()
            stream.close()
            pa.terminate()
            if self.sio and self.sio.connected:
                self.sio.disconnect()
            logger.info("👋 Jack AI band ho gaya.")


def main():
    # Handle Ctrl+C gracefully
    engine = JackVoiceEngine()

    def signal_handler(sig, frame):
        logger.info("\nSignal mila, band ho raha hoon...")
        engine.running = False
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    engine.run()


if __name__ == "__main__":
    main()
