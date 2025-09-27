#!/usr/bin/env python3
"""
Text-to-Speech service (OpenAI GPT-4o-mini-tts)

Maintains the legacy class name `AgoraTTSService` for backwards compatibility,
but internally uses OpenAI's GPT-4o-mini-tts endpoint to synthesize speech.
"""
import base64
import logging
from typing import Optional

import aiohttp

try:
    from langfuse import observe
    LANGFUSE_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    LANGFUSE_AVAILABLE = False

    def observe(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

from ..utils.config import Config


class AgoraTTSService:
    """Wrapper around OpenAI GPT-4o-mini-tts REST API."""

    def __init__(self, config: Config):
        self.logger = logging.getLogger(__name__)

        tts_cfg = getattr(config, "openai_tts", None)
        self.enabled = getattr(tts_cfg, "enabled", False)
        self.api_key = getattr(tts_cfg, "api_key", None)
        self.model = getattr(tts_cfg, "model", "gpt-4o-mini-tts")
        base_url = getattr(tts_cfg, "base_url", "https://api.openai.com") or "https://api.openai.com"
        self.base_url = base_url.rstrip("/")

        self.allowed_voices = {
            "alloy",
            "echo",
            "fable",
            "onyx",
            "nova",
            "shimmer",
            "coral",
            "verse",
            "ballad",
            "ash",
            "sage",
            "marin",
            "cedar",
        }
        self.voice_aliases = {
            "zh-cn-xiaoxiaoneural": "alloy",
            "zh-cn-xiaoyineural": "alloy",
            "azure-alloy": "alloy",
            "female": "nova",
            "male": "onyx",
        }
        configured_voice = getattr(tts_cfg, "default_voice", "alloy")
        self.default_voice = self._resolve_voice(configured_voice, fallback="alloy")
        self.audio_format = getattr(tts_cfg, "audio_format", "mp3") or "mp3"

    def _resolve_voice(self, voice: Optional[str], fallback: Optional[str] = None) -> str:
        fallback = (fallback or self.default_voice or "alloy").strip().lower()
        candidate = (voice or fallback or "alloy").strip().lower()

        mapped = self.voice_aliases.get(candidate)
        if mapped:
            return mapped

        if candidate in self.allowed_voices:
            return candidate

        if fallback in self.allowed_voices:
            self.logger.warning(f"Voice '{voice}' not supported. Falling back to '{fallback}'.")
            return fallback

        self.logger.warning(f"Voice '{voice}' not supported. Falling back to 'alloy'.")
        return "alloy"

    def _build_request_payload(self, text: str, voice: Optional[str], audio_format: Optional[str]) -> dict:
        return {
            "model": self.model,
            "input": text,
            "voice": self._resolve_voice(voice),
            "format": audio_format or self.audio_format
        }

    def _headers(self) -> dict:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def _post_tts(self, payload: dict) -> Optional[bytes]:
        url = f"{self.base_url}/v1/audio/speech"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self._headers(), timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    self.logger.error(f"OpenAI TTS request failed ({response.status}): {error_text}")
                    return None

                audio_bytes = await response.read()
                if not audio_bytes:
                    self.logger.error("OpenAI TTS response did not contain audio data")
                    return None

                return audio_bytes

    @observe(name="openai_tts_synthesis")
    async def synthesize_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        audio_format: Optional[str] = None
    ) -> Optional[bytes]:
        """Convert text to speech using OpenAI GPT-4o-mini-tts."""

        if not self.enabled:
            self.logger.info("OpenAI TTS disabled; skipping synthesis")
            return None

        if not text:
            return None

        try:
            payload = self._build_request_payload(text, voice, audio_format)
            audio_bytes = await self._post_tts(payload)
            if audio_bytes:
                self.logger.debug(f"OpenAI TTS produced {len(audio_bytes)} bytes")
            return audio_bytes
        except Exception as exc:  # pragma: no cover - network interaction
            self.logger.error(f"OpenAI TTS synthesis error: {exc}")
            return None

    @observe(name="openai_tts_simple")
    async def text_to_speech(self, text: str, voice: Optional[str] = None, audio_format: Optional[str] = None) -> Optional[str]:
        audio_bytes = await self.synthesize_speech(text, voice=voice, audio_format=audio_format)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode()
        return None

    async def save_audio_file(self, text: str, filepath: str, voice: Optional[str] = None, audio_format: Optional[str] = None) -> bool:
        audio_bytes = await self.synthesize_speech(text, voice=voice, audio_format=audio_format)
        if not audio_bytes:
            return False

        try:
            with open(filepath, "wb") as handle:
                handle.write(audio_bytes)
            self.logger.info(f"Saved OpenAI TTS audio to {filepath}")
            return True
        except Exception as exc:  # pragma: no cover - file IO
            self.logger.error(f"Failed to save OpenAI TTS audio: {exc}")
            return False
