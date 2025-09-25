#!/usr/bin/env python3
"""
Minimal Processor - Ultra-simple processing to avoid API overload
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
import time
import anthropic

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
from .context_manager import SystemContext


class MinimalProcessor:
    """Ultra-minimal processor to avoid API overload issues"""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.claude_client = anthropic.Anthropic(
            api_key=config.anthropic.api_key,
            max_retries=1,  # Reduce retries
            timeout=10.0    # Reduce timeout
        )

        # Load character prompt
        self.character_prompt = self._load_prompt_file('prompts/character.txt')

        # API rate limiting
        self.last_call_time = 0
        self.min_interval = 2.0  # Minimum 2 seconds between calls

    def _load_prompt_file(self, filepath: str) -> str:
        """Load prompt from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Failed to load prompt file {filepath}: {e}")
            return "你是凌波丽，智能家居助手。回复简洁、内敛。"

    async def _rate_limit(self):
        """Simple rate limiting to avoid API overload"""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time

        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            self.logger.info(f"Rate limiting: waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)

        self.last_call_time = time.time()

    @observe(as_type="generation", name="minimal_processing")
    async def process_minimal(
        self,
        user_input: str,
        context: SystemContext
    ) -> Dict[str, Any]:
        """Ultra-minimal processing with rate limiting"""

        # Rate limit to avoid overload
        await self._rate_limit()

        self.logger.info(f"Minimal processing: {user_input}")

        # Get basic context
        familiarity = context.familiarity_score

        # Ultra-simple prompt
        prompt = f"""用户: "{user_input}"
熟悉度: {familiarity}/100

简短回复。如需控制设备且熟悉度≥40，说明设备和操作。"""

        try:
            # Simple non-streaming call with minimal settings
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model="claude-3-haiku-20240307",  # Use faster model
                max_tokens=100,  # Very limited
                temperature=0.1,  # Low temperature
                system="你是凌波丽。简洁回复。",
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Simple device detection
            involves_hardware = any(device in user_input for device in
                                  ["空调", "灯", "电视", "音响", "窗帘", "air", "light", "tv"])

            # Simple action detection
            action = None
            if "开" in user_input or "打开" in user_input or "turn_on" in user_input.lower():
                action = "turn_on"
            elif "关" in user_input or "关闭" in user_input or "turn_off" in user_input.lower():
                action = "turn_off"

            # Simple device detection
            device = None
            if "空调" in user_input or "air" in user_input.lower():
                device = "air_conditioner"
            elif "灯" in user_input or "light" in user_input.lower():
                device = "lights"
            elif "电视" in user_input or "tv" in user_input.lower():
                device = "tv"

            # Check familiarity for device control
            can_control = familiarity >= 40 and involves_hardware and device and action

            intent_analysis = {
                "involves_hardware": involves_hardware,
                "device": device if can_control else None,
                "action": action if can_control else None,
                "parameters": {},
                "confidence": 0.8,
                "familiarity_check": "passed" if can_control else "failed" if involves_hardware else "not_needed"
            }

            # Update context
            context.add_conversation_turn(user_input, response_text)
            if involves_hardware:
                context.add_intent(intent_analysis)

            self.logger.info(f"Minimal processing result: device={device}, action={action}, can_control={can_control}")

            return {
                "response": response_text,
                "intent_analysis": intent_analysis,
                "device_actions": [],
                "metadata": {
                    "minimal_mode": True,
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 100,
                    "processing_type": "minimal_safe",
                    "familiarity_score": familiarity,
                    "rate_limited": True
                }
            }

        except Exception as e:
            self.logger.error(f"Minimal processing error: {e}")

            # Fallback response without API call
            return {
                "response": "......我明白了。" if familiarity >= 40 else "......抱歉，我现在无法处理。",
                "intent_analysis": {
                    "involves_hardware": False,
                    "device": None,
                    "action": None,
                    "confidence": 0.1,
                    "familiarity_check": "error"
                },
                "device_actions": [],
                "metadata": {
                    "minimal_mode": True,
                    "error": str(e),
                    "fallback_used": True
                }
            }