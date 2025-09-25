#!/usr/bin/env python3
"""
Agora (声网) TTS Service
Text-to-Speech using Agora REST API
"""
import asyncio
import json
import logging
import base64
import hashlib
import hmac
import time
from typing import Optional, Dict, Any
import aiohttp

try:
    from langfuse import observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from ..utils.config import Config


class AgoraTTSService:
    """Agora Text-to-Speech service"""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.app_key = config.agora.app_key if hasattr(config, 'agora') else None
        self.app_secret = config.agora.app_secret if hasattr(config, 'agora') else None
        self.enabled = config.agora.enabled if hasattr(config, 'agora') else False

        # Agora TTS API endpoints
        self.base_url = "https://api.agora.io"
        self.tts_endpoint = "/v1/projects/{}/tts-tasks"

    def _generate_signature(self, method: str, url: str, body: str = "") -> Dict[str, str]:
        """Generate Agora API signature"""
        timestamp = str(int(time.time()))
        nonce = str(int(time.time() * 1000))

        # Create signature string
        sig_string = f"{method}\n{url}\n{body}\n{self.app_key}\n{timestamp}\n{nonce}"

        # Generate HMAC-SHA256 signature
        signature = base64.b64encode(
            hmac.new(
                self.app_secret.encode(),
                sig_string.encode(),
                hashlib.sha256
            ).digest()
        ).decode()

        return {
            "X-Agora-Key": self.app_key,
            "X-Agora-Timestamp": timestamp,
            "X-Agora-Nonce": nonce,
            "X-Agora-Signature": signature,
            "Content-Type": "application/json"
        }

    @observe(name="agora_tts_synthesis")
    async def synthesize_speech(
        self,
        text: str,
        voice: str = "zh-CN-XiaoxiaoNeural",
        format: str = "mp3"
    ) -> Optional[bytes]:
        """Convert text to speech using Agora TTS"""

        if not self.enabled or not self.app_key or not self.app_secret:
            self.logger.warning("Agora TTS not configured or disabled")
            return None

        try:
            self.logger.info(f"Starting TTS synthesis for text: {text[:50]}...")

            # Prepare request body
            request_body = {
                "text": text,
                "voice": voice,
                "format": format,
                "sample_rate": 16000,
                "speed": 1.0,
                "pitch": 0,
                "volume": 100
            }

            body_json = json.dumps(request_body)
            url_path = self.tts_endpoint.format("your_project_id")  # Replace with actual project ID
            full_url = self.base_url + url_path

            # Generate signature
            headers = self._generate_signature("POST", url_path, body_json)

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    full_url,
                    headers=headers,
                    data=body_json,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status == 200:
                        result = await response.json()

                        # Check if synthesis was successful
                        if result.get("code") == 200:
                            # Get audio data
                            audio_url = result.get("data", {}).get("audio_url")
                            if audio_url:
                                # Download audio
                                async with session.get(audio_url) as audio_response:
                                    if audio_response.status == 200:
                                        audio_data = await audio_response.read()
                                        self.logger.info(f"TTS synthesis successful, audio size: {len(audio_data)} bytes")
                                        return audio_data
                                    else:
                                        self.logger.error(f"Failed to download audio: {audio_response.status}")
                            else:
                                self.logger.error("No audio URL in response")
                        else:
                            self.logger.error(f"TTS synthesis failed: {result}")
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Agora API error {response.status}: {error_text}")

        except Exception as e:
            self.logger.error(f"TTS synthesis error: {e}")

        return None

    @observe(name="agora_tts_simple")
    async def text_to_speech(self, text: str) -> Optional[str]:
        """Simple text to speech - returns base64 encoded audio"""

        audio_data = await self.synthesize_speech(text)
        if audio_data:
            # Return base64 encoded audio for easy transmission
            return base64.b64encode(audio_data).decode()
        return None

    async def save_audio_file(self, text: str, filepath: str) -> bool:
        """Save TTS audio to file"""

        audio_data = await self.synthesize_speech(text)
        if audio_data:
            try:
                with open(filepath, 'wb') as f:
                    f.write(audio_data)
                self.logger.info(f"Audio saved to {filepath}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to save audio file: {e}")
        return False