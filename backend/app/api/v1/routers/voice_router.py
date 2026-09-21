"""Voice interview endpoints — Azure Speech STT/TTS."""
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from app.core.rbac import CurrentUser, get_current_user
from app.infrastructure.azure_speech.speech_service import get_speech_service

router = APIRouter(prefix="/voice", tags=["voice"])


class TextToSpeechRequest(BaseModel):
    text: str


class SpeechToTextResponse(BaseModel):
    text: str


@router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(
    audio: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    audio_bytes = await audio.read()
    service = get_speech_service()
    text = await service.speech_to_text(audio_bytes)
    return SpeechToTextResponse(text=text)


@router.post("/text-to-speech")
async def text_to_speech(
    payload: TextToSpeechRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    service = get_speech_service()
    audio_bytes = await service.text_to_speech(payload.text)
    return Response(content=audio_bytes, media_type="audio/mpeg")
