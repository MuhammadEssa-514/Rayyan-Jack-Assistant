"""
Jack AI Voice Engine — Speech Recognition Module
Uses Faster-Whisper for fast, offline, multilingual STT.
Supports Urdu, English, Roman Urdu.
"""
import io
import numpy as np
from loguru import logger
from pathlib import Path

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.error("faster-whisper not installed: pip install faster-whisper")


class SpeechRecognizer:
    """
    Offline speech recognition using Faster-Whisper.
    Model: 'small' recommended for best speed+accuracy on Urdu.
    """

    def __init__(
        self,
        model_size: str = "small",
        device: str = "auto",
        compute_type: str = "int8",
        language: str = None,
    ):
        self.model_size = model_size
        self.language = language  # None = auto-detect
        self.model = None

        # Resolve device
        if device == "auto":
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self.device = "cpu"
        else:
            self.device = device

        # int8 is fastest on CPU, float16 on GPU
        self.compute_type = "float16" if self.device == "cuda" else compute_type

    def initialize(self):
        """Load the Whisper model (downloads on first run)."""
        if not WHISPER_AVAILABLE:
            logger.error("faster-whisper not available!")
            return False

        try:
            logger.info(f"🔄 Whisper '{self.model_size}' load ho raha hai ({self.device})...")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=str(Path(__file__).parent.parent / "models" / "whisper"),
            )
            logger.success(f"✅ Whisper ready: {self.model_size} on {self.device}")
            return True
        except Exception as e:
            logger.error(f"❌ Whisper load nahi hua: {e}")
            return False

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> dict:
        """
        Transcribe audio to text.

        Args:
            audio_data: numpy array of float32 audio samples
            sample_rate: audio sample rate (must be 16000 for Whisper)

        Returns:
            dict with 'text', 'language', 'confidence'
        """
        if self.model is None:
            success = self.initialize()
            if not success:
                return {"text": "", "language": "unknown", "confidence": 0}

        try:
            # Ensure float32 in [-1, 1]
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            # Whisper transcription
            segments, info = self.model.transcribe(
                audio_data,
                language=self.language,  # None = auto-detect
                beam_size=3,             # Lower = faster (default 5)
                best_of=3,
                vad_filter=True,         # Filter out silence
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200,
                ),
                condition_on_previous_text=False,  # Faster
                word_timestamps=False,
                without_timestamps=True,
            )

            # Collect all segments
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())

            full_text = " ".join(text_parts).strip()

            # Calculate average confidence
            confidence = info.language_probability if info else 0.8

            logger.info(f"📝 Transcribed [{info.language if info else '?'}]: \"{full_text}\"")

            return {
                "text": full_text,
                "language": info.language if info else "unknown",
                "confidence": float(confidence),
            }

        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            return {"text": "", "language": "unknown", "confidence": 0}

    def is_ready(self) -> bool:
        return self.model is not None
