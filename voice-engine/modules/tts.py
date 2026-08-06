"""
Jack AI Voice Engine — Text-to-Speech Module
Uses Piper TTS for fast, offline, natural-sounding speech.
Supports Urdu and English voices.
"""
import subprocess
import tempfile
import os
import threading
from pathlib import Path
# pyrefly: ignore [missing-import]
from loguru import logger

try:
    # pyrefly: ignore [missing-import]
    import pygame
    PYGAME_AVAILABLE = True
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
except ImportError:
    PYGAME_AVAILABLE = False
    logger.warning("pygame not available — using subprocess audio playback")


class TTSEngine:
    """
    Text-to-Speech using Piper TTS.

    Download Urdu model:
    https://huggingface.co/rhasspy/piper-voices/tree/main/ur/ur_PK/usman/medium

    Download English fallback:
    https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/lessac/medium
    """

    def __init__(self, model_path: str, config_path: str = None):
        self.model_path = Path(model_path)
        self.config_path = Path(config_path) if config_path else Path(str(model_path) + ".json")
        self._lock = threading.Lock()
        self._ready = False
        self._check_model()

    def _check_model(self):
        """Check if Piper model exists."""
        if self.model_path.exists():
            self._ready = True
            logger.success(f"✅ TTS model ready: {self.model_path.name}")
        else:
            logger.warning(f"⚠️  TTS model nahi mila: {self.model_path}")
            logger.info("💡 Model download karo:")
            logger.info("   https://huggingface.co/rhasspy/piper-voices")
            logger.info(f"   File yahan rakhna: {self.model_path}")
            self._ready = False

    def speak(self, text: str, blocking: bool = False):
        """
        Speak the given text.

        Args:
            text: Text to speak (Urdu or English)
            blocking: If True, wait for speech to complete
        """
        if not text or not text.strip():
            return

        if blocking:
            self._speak_sync(text)
        else:
            thread = threading.Thread(target=self._speak_sync, args=(text,), daemon=True)
            thread.start()

    def _speak_sync(self, text: str):
        """Synchronously generate and play TTS audio."""
        with self._lock:
            try:
                if not self._ready:
                    # Fallback: print to console
                    logger.info(f"🔊 [TTS Fallback] {text}")
                    self._system_speak(text)
                    return

                # Generate audio with Piper
                audio_data = self._generate_audio(text)

                if audio_data:
                    self._play_audio(audio_data)

            except Exception as e:
                logger.error(f"TTS error: {e}")
                self._system_speak(text)

    def _generate_audio(self, text: str) -> bytes:
        """Generate WAV audio using Piper."""
        try:
            # Use piper as subprocess
            cmd = [
                "piper",
                "--model", str(self.model_path),
                "--output_raw",
            ]

            result = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=15,
            )

            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"Piper error: {result.stderr.decode()}")
                return None

        except FileNotFoundError:
            logger.error("Piper not found! Install: pip install piper-tts")
            return None
        except subprocess.TimeoutExpired:
            logger.error("Piper timeout!")
            return None

    def _play_audio(self, audio_data: bytes):
        """Play raw PCM audio data."""
        try:
            if PYGAME_AVAILABLE:
                # Create sound from raw PCM (22050Hz, 16-bit, mono)
                import io
                sound = pygame.mixer.Sound(buffer=audio_data)
                channel = sound.play()
                while channel.get_busy():
                    pygame.time.wait(50)
            else:
                # Fallback: write to temp file and play with system player
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio_data)
                    tmp_path = f.name

                # Windows: use powershell to play
                subprocess.run(
                    ["powershell", "-c", f"(New-Object Media.SoundPlayer '{tmp_path}').PlaySync()"],
                    timeout=30
                )
                os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"Audio playback error: {e}")

    def _system_speak(self, text: str):
        """Last resort: use Windows SAPI TTS."""
        try:
            cmd = f'Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak("{text}")'
            subprocess.run(
                ["powershell", "-c", cmd],
                timeout=10,
                capture_output=True,
            )
        except Exception:
            pass  # TTS completely failed - non-critical

    def is_ready(self) -> bool:
        return self._ready
