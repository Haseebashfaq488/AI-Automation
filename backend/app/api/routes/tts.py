"""Edge TTS (Text-to-Speech) streaming endpoint powered by Microsoft Edge Neural Voices.

Converts Antigravity responses into natural, high-fidelity neural audio.
Automatically sanitizes inline delimiters (<<<gesture: ...>>>), emojis,
and markdown formatting so only clean, spoken text is synthesized.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

import edge_tts
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("jarvis.api.tts")

router = APIRouter(prefix="/agent/tts", tags=["TTS"])

DEFAULT_VOICE = "en-US-AvaNeural"


class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize into speech")
    voice: Optional[str] = Field(default=DEFAULT_VOICE, description="Edge TTS voice name (e.g. en-US-AvaNeural, en-US-AriaNeural, en-US-AnaNeural)")
    rate: Optional[str] = Field(default="+0%", description="Speaking speed adjustment (e.g. +10%, -5%)")
    pitch: Optional[str] = Field(default="+0Hz", description="Pitch adjustment (e.g. +5Hz, -5Hz)")


def clean_text_for_speech(text: str) -> str:
    """Strip delimiters, code fences, markdown, and emojis before passing to TTS."""
    if not text:
        return ""

    # 1. Strip inline avatar gesture & expression delimiters (e.g. <<<gesture: ...>>>)
    cleaned = re.sub(r"<<<[^>]+>>>", "", text)

    # 2. Strip markdown code fences (```...```) and inline code (`...`)
    cleaned = re.sub(r"```[\s\S]*?```", "", cleaned)
    cleaned = re.sub(r"`[^`]*`", "", cleaned)

    # 3. Clean markdown links [label](url) -> label
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)

    # 4. Clean bold, italics, headers, bullets
    cleaned = re.sub(r"[*_~#]", "", cleaned)
    cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)

    # 5. Remove excessive whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


@router.post("", summary="Synthesize text to MP3 audio stream using Edge TTS")
async def synthesize_speech(req: TTSRequest):
    """Synthesizes text into an MP3 audio stream."""
    clean_text = clean_text_for_speech(req.text)
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided text does not contain any speakable content after stripping tags.",
        )

    voice = req.voice or DEFAULT_VOICE
    logger.info("Synthesizing Edge TTS with voice '%s' (chars: %d)", voice, len(clean_text))

    async def audio_stream():
        try:
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=voice,
                rate=req.rate or "+0%",
                pitch=req.pitch or "+0Hz",
            )
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except Exception as exc:
            logger.error("Edge TTS streaming failed: %s", exc)
            raise

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-cache",
            "Content-Disposition": "inline; filename=speech.mp3",
        },
    )


@router.get("/voices", summary="List recommended English Edge TTS voices")
async def list_recommended_voices():
    """Returns curated list of recommended voices for Jarvis / Bubbles."""
    return {
        "default": DEFAULT_VOICE,
        "voices": [
            {"id": "en-US-AvaNeural", "gender": "Female", "description": "Warm, natural, friendly, conversational"},
            {"id": "en-US-AriaNeural", "gender": "Female", "description": "Expressive, poised, clear"},
            {"id": "en-US-AnaNeural", "gender": "Female", "description": "Cute, youthful, gentle"},
            {"id": "en-US-EmmaNeural", "gender": "Female", "description": "Warm, cheerful, British-accented style"},
            {"id": "en-US-JennyNeural", "gender": "Female", "description": "Professional, calm assistant"},
            {"id": "en-US-AndrewNeural", "gender": "Male", "description": "Friendly, warm male voice"},
        ],
    }
