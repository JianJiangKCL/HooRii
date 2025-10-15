#!/usr/bin/env python3
"""
Text-to-Speech service abstraction for multiple providers.

Maintains the legacy class name `AgoraTTSService` for backwards compatibility
with existing imports. Supports OpenAI GPT-4o-mini-tts and ElevenLabs.
"""
import base64
import logging
from typing import Optional

import aiohttp

from ..utils.text_formatting import format_text_for_tts

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
    """Wrapper around the configured text-to-speech provider."""

    def __init__(self, config: Config):
        self.logger = logging.getLogger(__name__)
        self.config = config

        selection_cfg = getattr(config, "tts", None)
        self.provider = (getattr(selection_cfg, "provider", "openai") or "openai").strip().lower()
        self.enabled = bool(getattr(selection_cfg, "enabled", False))
        self.default_voice = getattr(selection_cfg, "default_voice", None)
        self.audio_format = (getattr(selection_cfg, "audio_format", "mp3") or "mp3").strip().lower()

        self._openai_cfg = getattr(config, "openai_tts", None)
        self._elevenlabs_cfg = getattr(config, "elevenlabs_tts", None)

        # Common attributes initialised for both providers
        self.api_key: Optional[str] = None
        self.model: Optional[str] = None
        self.base_url: Optional[str] = None
        self.output_format: Optional[str] = None
        self.allowed_voices = set()
        self.voice_aliases = {}
        self.voice_settings = {}
        self.style_preset: Optional[str] = None
        self.optimize_streaming_latency: Optional[int] = None

        if self.provider == "openai":
            self._configure_openai()
        elif self.provider == "elevenlabs":
            self._configure_elevenlabs()
        else:
            if self.enabled:
                self.logger.warning("Unsupported TTS provider '%s'. Disabling TTS.", self.provider)
            self.enabled = False

    # ---------------------------------------------------------------------
    # Provider configuration
    # ---------------------------------------------------------------------
    def _configure_openai(self) -> None:
        cfg = self._openai_cfg
        if not cfg or not getattr(cfg, "api_key", None) or not getattr(cfg, "enabled", False):
            self.logger.warning("OpenAI TTS configuration missing or disabled. Provider unavailable.")
            self.enabled = False
            return

        self.enabled = self.enabled and cfg.enabled
        self.api_key = cfg.api_key
        self.model = cfg.model
        self.base_url = (cfg.base_url or "https://api.openai.com").rstrip("/")
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
        fallback_voice = self.default_voice or cfg.default_voice or "alloy"
        self.default_voice = self._resolve_openai_voice(fallback_voice, fallback="alloy")
        self.audio_format = (self.audio_format or cfg.audio_format or "mp3").lower()

    def _configure_elevenlabs(self) -> None:
        cfg = self._elevenlabs_cfg
        if not cfg or not getattr(cfg, "api_key", None) or not getattr(cfg, "voice_id", None) or not getattr(cfg, "enabled", False):
            self.logger.warning("ElevenLabs TTS configuration missing or disabled. Provider unavailable.")
            self.enabled = False
            return

        self.enabled = self.enabled and cfg.enabled
        self.api_key = cfg.api_key
        self.model = cfg.model
        self.base_url = (cfg.base_url or "https://api.elevenlabs.io").rstrip("/")
        self.output_format = cfg.output_format or "mp3_44100_128"
        self.voice_settings = cfg.voice_settings or {}
        self.style_preset = cfg.style_preset
        self.optimize_streaming_latency = cfg.optimize_streaming_latency
        # Use the ElevenLabs voice_id directly, not the generic default_voice
        self.default_voice = cfg.voice_id
        if not self.audio_format:
            self.audio_format = "mp3"

    # ---------------------------------------------------------------------
    # Voice resolution helpers
    # ---------------------------------------------------------------------
    def _resolve_openai_voice(self, voice: Optional[str], fallback: Optional[str] = None) -> str:
        fallback_voice = (fallback or self.default_voice or "alloy").strip().lower()
        candidate = (voice or fallback_voice or "alloy").strip().lower()

        mapped = self.voice_aliases.get(candidate)
        if mapped:
            return mapped

        if candidate in self.allowed_voices:
            return candidate

        if fallback_voice in self.allowed_voices:
            if candidate != fallback_voice:
                self.logger.warning("Voice '%s' not supported. Falling back to '%s'.", voice, fallback_voice)
            return fallback_voice

        self.logger.warning("Voice '%s' not supported. Falling back to 'alloy'.", voice)
        return "alloy"

    def _resolve_voice(self, voice: Optional[str], fallback: Optional[str] = None) -> Optional[str]:
        if self.provider == "openai":
            return self._resolve_openai_voice(voice, fallback=fallback)

        resolved = (voice or fallback or self.default_voice or "").strip()
        if not resolved:
            self.logger.error("No ElevenLabs voice ID available; please configure ELEVENLABS_VOICE_ID.")
        return resolved or None

    # ---------------------------------------------------------------------
    # OpenAI implementation
    # ---------------------------------------------------------------------
    def _build_openai_payload(self, text: str, voice: Optional[str], audio_format: Optional[str]) -> dict:
        return {
            "model": self.model,
            "input": text,
            "voice": self._resolve_voice(voice),
            "format": (audio_format or self.audio_format or "mp3"),
        }

    def _openai_headers(self) -> dict:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _post_openai_tts(self, payload: dict) -> Optional[bytes]:
        url = f"{self.base_url}/v1/audio/speech"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers=self._openai_headers(),
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    self.logger.error("OpenAI TTS request failed (%s): %s", response.status, error_text)
                    return None

                audio_bytes = await response.read()
                if not audio_bytes:
                    self.logger.error("OpenAI TTS response did not contain audio data")
                    return None

                return audio_bytes

    async def _synthesize_openai(self, text: str, voice: Optional[str], audio_format: Optional[str]) -> Optional[bytes]:
        payload = self._build_openai_payload(text, voice, audio_format)
        audio_bytes = await self._post_openai_tts(payload)
        if audio_bytes:
            self.logger.debug("OpenAI TTS produced %d bytes", len(audio_bytes))
        return audio_bytes

    # ---------------------------------------------------------------------
    # ElevenLabs implementation
    # ---------------------------------------------------------------------
    def _map_elevenlabs_output_format(self, requested: Optional[str]) -> str:
        if requested:
            requested_lower = requested.lower()
            mapping = {
                "mp3": "mp3_44100_128",
                "mp3_44100_128": "mp3_44100_128",
                "mp3_44100_64": "mp3_44100_64",
                "mp3_22050_32": "mp3_22050_32",
                "wav": "pcm_44100",
                "pcm": "pcm_44100",
                "pcm_44100": "pcm_44100",
                "pcm_16000": "pcm_16000",
                "pcm_22050": "pcm_22050",
                "ulaw": "ulaw_8000",
                "ulaw_8000": "ulaw_8000",
                "ogg": "ogg_44100",
                "ogg_44100": "ogg_44100",
            }
            if requested_lower in mapping:
                return mapping[requested_lower]
            # Allow passing the ElevenLabs value directly
            if requested in mapping.values():
                return requested

        return self.output_format or "mp3_44100_128"

    def _elevenlabs_headers(self, output_format: str) -> dict:
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY is not configured")

        accept = "application/octet-stream"
        normalized = (output_format or "").lower()
        if normalized.startswith("mp3"):
            accept = "audio/mpeg"
        elif normalized.startswith("pcm") or normalized == "wav":
            accept = "audio/wav"
        elif normalized.startswith("ogg"):
            accept = "audio/ogg"
        elif normalized.startswith("ulaw"):
            accept = "audio/basic"

        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": accept,
        }

    def _build_elevenlabs_payload(
        self,
        text: str,
        voice: Optional[str],
        audio_format: Optional[str],
    ) -> Optional[tuple]:
        voice_id = self._resolve_voice(voice)
        if not voice_id:
            return None

        output_format = self._map_elevenlabs_output_format(audio_format)
        payload = {
            "text": text,
            "model_id": self.model or "eleven_multilingual_v2",
        }
        if self.voice_settings:
            payload["voice_settings"] = self.voice_settings
        if self.style_preset:
            payload["style_preset"] = self.style_preset
        query_params = {"output_format": output_format}
        if self.optimize_streaming_latency is not None:
            query_params["optimize_streaming_latency"] = str(self.optimize_streaming_latency)

        return payload, voice_id, output_format, query_params

    async def _post_elevenlabs_tts(
        self,
        payload: dict,
        voice_id: str,
        output_format: str,
        query_params: Optional[dict],
    ) -> Optional[bytes]:
        url = f"{self.base_url}/v1/text-to-speech/{voice_id}"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                params=query_params or None,
                headers=self._elevenlabs_headers(output_format),
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    self.logger.error("ElevenLabs TTS request failed (%s): %s", response.status, error_text)
                    return None

                audio_bytes = await response.read()
                if not audio_bytes:
                    self.logger.error("ElevenLabs TTS response did not contain audio data")
                    return None

                return audio_bytes

    async def _synthesize_elevenlabs(self, text: str, voice: Optional[str], audio_format: Optional[str]) -> Optional[bytes]:
        payload_info = self._build_elevenlabs_payload(text, voice, audio_format)
        if not payload_info:
            return None

        payload, voice_id, output_format, query_params = payload_info
        audio_bytes = await self._post_elevenlabs_tts(payload, voice_id, output_format, query_params)
        if audio_bytes:
            self.logger.debug("ElevenLabs TTS produced %d bytes", len(audio_bytes))
        return audio_bytes

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    @observe(name="tts_synthesis")
    async def synthesize_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        audio_format: Optional[str] = None,
    ) -> Optional[bytes]:
        if not self.enabled:
            self.logger.info("TTS provider '%s' disabled; skipping synthesis", self.provider)
            return None

        if not text:
            return None

        text = text.strip()
        if not text:
            return None

        # Format text for the specific TTS provider (adds SSML markers for ElevenLabs)
        formatted_text = format_text_for_tts(text, self.provider)
        
        # Log if text was modified
        if formatted_text != text:
            self.logger.debug(f"Text formatted for {self.provider}: {text[:50]}... -> {formatted_text[:50]}...")

        try:
            if self.provider == "openai":
                return await self._synthesize_openai(formatted_text, voice, audio_format)
            if self.provider == "elevenlabs":
                return await self._synthesize_elevenlabs(formatted_text, voice, audio_format)

            self.logger.error("No supported TTS provider configured")
            return None
        except Exception as exc:  # pragma: no cover - network interaction
            self.logger.error("%s TTS synthesis error: %s", self.provider.title(), exc)
            return None

    @observe(name="tts_simple")
    async def text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        audio_format: Optional[str] = None,
    ) -> Optional[str]:
        audio_bytes = await self.synthesize_speech(text, voice=voice, audio_format=audio_format)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode()
        return None

    async def save_audio_file(
        self,
        text: str,
        filepath: str,
        voice: Optional[str] = None,
        audio_format: Optional[str] = None,
    ) -> bool:
        audio_bytes = await self.synthesize_speech(text, voice=voice, audio_format=audio_format)
        if not audio_bytes:
            return False

        try:
            with open(filepath, "wb") as handle:
                handle.write(audio_bytes)
            self.logger.info("Saved %s TTS audio to %s", self.provider.title(), filepath)
            return True
        except Exception as exc:  # pragma: no cover - file IO
            self.logger.error("Failed to save %s TTS audio: %s", self.provider.title(), exc)
            return False
