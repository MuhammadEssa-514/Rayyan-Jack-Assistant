"""
Jack AI Voice Engine — Wake Word Detection Module
Uses OpenWakeWord for offline, lightweight wake word detection.
"""
import numpy as np
from loguru import logger

try:
    import openwakeword
    from openwakeword.model import Model as OWWModel
    OWW_AVAILABLE = True
except ImportError:
    OWW_AVAILABLE = False
    logger.warning("OpenWakeWord not installed. Using keyword fallback.")

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False


class WakeWordDetector:
    """
    Detects the wake word using OpenWakeWord.
    Falls back to a simple keyword-in-text method if OWW is unavailable.
    """

    def __init__(self, wake_word: str = "hey_jarvis", threshold: float = 0.5):
        self.wake_word = wake_word
        self.threshold = threshold
        self.model = None
        self._initialized = False

    def initialize(self):
        """Load the wake word model."""
        if not OWW_AVAILABLE:
            logger.warning("⚠️  OpenWakeWord unavailable — using text-based fallback")
            self._initialized = True
            return

        try:
            logger.info(f"🔄 Wake word model load ho raha hai: {self.wake_word}")
            # Download and cache model automatically
            self.model = OWWModel(
                wakeword_models=[self.wake_word],
                enable_speex_noise_suppression=False,  # Disable for speed
            )
            self._initialized = True
            logger.success(f"✅ Wake word model ready: '{self.wake_word}'")
        except Exception as e:
            logger.error(f"❌ Wake word model load nahi hua: {e}")
            logger.info("💡 Fallback mode mein chal raha hai")
            self._initialized = True

    def detect(self, audio_chunk: np.ndarray) -> bool:
        """
        Process an audio chunk and return True if wake word detected.
        audio_chunk: numpy array, int16, 16kHz mono
        """
        if not self._initialized:
            self.initialize()

        if self.model is None:
            return False

        try:
            # OpenWakeWord expects int16 numpy array
            if audio_chunk.dtype != np.int16:
                audio_chunk = (audio_chunk * 32767).astype(np.int16)

            prediction = self.model.predict(audio_chunk)

            # Check score for our wake word
            score = prediction.get(self.wake_word, 0)

            if score >= self.threshold:
                logger.info(f"🎯 Wake word detected! Score: {score:.2f}")
                self.model.reset()  # Reset state after detection
                return True

        except Exception as e:
            logger.error(f"Wake word detection error: {e}")

        return False

    def reset(self):
        """Reset model state (call after wake word detected)."""
        if self.model:
            try:
                self.model.reset()
            except Exception:
                pass

    def text_fallback_detect(self, text: str) -> bool:
        """
        Simple text-based fallback: check if "Jack" appears in transcribed text.
        Used when OpenWakeWord is not available.
        """
        keywords = ["jack", "جیک", "hey jack", "hy jack"]
        text_lower = text.lower().strip()
        return any(kw in text_lower for kw in keywords)
