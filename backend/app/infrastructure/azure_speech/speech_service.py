"""Azure Speech Service wrapper for Speech-to-Text and Text-to-Speech."""
from __future__ import annotations

import asyncio
import io

import azure.cognitiveservices.speech as speechsdk

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AzureSpeechService:
    def __init__(self) -> None:
        settings = get_settings()
        self._speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_speech_key, region=settings.azure_speech_region
        )
        self._speech_config.speech_synthesis_voice_name = settings.azure_speech_voice

    async def speech_to_text(self, audio_bytes: bytes) -> str:
        """Transcribe raw WAV audio bytes to text."""
        return await asyncio.to_thread(self._speech_to_text_sync, audio_bytes)

    def _speech_to_text_sync(self, audio_bytes: bytes) -> str:
        stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=stream)
        recognizer = speechsdk.SpeechRecognizer(speech_config=self._speech_config, audio_config=audio_config)

        stream.write(audio_bytes)
        stream.close()

        result = recognizer.recognize_once()
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        if result.reason == speechsdk.ResultReason.NoMatch:
            logger.warning("speech_to_text_no_match")
            return ""
        raise RuntimeError(f"Speech recognition failed: {result.reason}")

    async def text_to_speech(self, text: str) -> bytes:
        """Synthesize `text` into MP3 audio bytes."""
        return await asyncio.to_thread(self._text_to_speech_sync, text)

    def _text_to_speech_sync(self, text: str) -> bytes:
        self._speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=self._speech_config, audio_config=None)
        result = synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        raise RuntimeError(f"Speech synthesis failed: {result.reason}")


_service: AzureSpeechService | None = None


def get_speech_service() -> AzureSpeechService:
    global _service
    if _service is None:
        _service = AzureSpeechService()
    return _service
