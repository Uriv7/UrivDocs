"""
UrivDocs — ingestion/parsers/audio.py
Audio/video transcription using faster-whisper (runs locally, no API).
faster-whisper is faster than openai-whisper and works on CPU with int8.
"""

from pathlib import Path
from typing import List

from loguru import logger

from ingestion.parsers.base import BasePage


class AudioParser:
    _model = None

    def _get_model(self):
        if AudioParser._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info("Loading faster-whisper model (base)...")
                AudioParser._model = WhisperModel("base", device="cpu", compute_type="int8")
            except ImportError:
                logger.error("faster-whisper not installed. Run: pip install faster-whisper")
                return None
        return AudioParser._model

    def parse(self, path: Path) -> List[BasePage]:
        model = self._get_model()
        if model is None:
            return [BasePage(text="[Audio transcription unavailable]", page_number=1)]

        try:
            logger.info(f"Transcribing {path.name}...")
            segments, info = model.transcribe(str(path), beam_size=5)
            logger.info(f"Detected language: {info.language} ({info.language_probability:.0%})")

            pages: List[BasePage] = []
            buffer: List[str] = []
            page_num = 1
            window_end = 60.0

            for seg in segments:
                buffer.append(seg.text.strip())
                if seg.end >= window_end:
                    pages.append(BasePage(
                        text=" ".join(buffer),
                        page_number=page_num,
                        section=f"{int(window_end - 60)}s – {int(window_end)}s",
                        extra={"language": info.language},
                    ))
                    buffer = []
                    page_num += 1
                    window_end += 60.0

            if buffer:
                pages.append(BasePage(text=" ".join(buffer), page_number=page_num))

            logger.info(f"Transcribed {len(pages)} segment(s) from {path.name}")
            return pages

        except Exception as e:
            logger.error(f"Audio transcription failed for {path.name}: {e}")
            return []
