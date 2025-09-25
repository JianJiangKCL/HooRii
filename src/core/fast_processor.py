#!/usr/bin/env python3
"""
Fast Processor Component (Fixed JSON parsing)
Combines intent analysis and response generation in a single LLM call for speed
"""
import asyncio
import json
import logging
import re
from typing import Dict, Any, Optional
import anthropic

# Try to import Langfuse components
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


class FastProcessor:
    """Single-pass LLM processor for fast responses"""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.claude_client = anthropic.Anthropic(
            api_key=config.anthropic.api_key,
            max_retries=2,
            timeout=15.0
        )

        # Load character prompt
        self.character_prompt = self._load_prompt_file('prompts/character.txt')

    def _load_prompt_file(self, filepath: str) -> str:
        """Load prompt from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Failed to load prompt file {filepath}: {e}")
            return "你是凌波丽，智能家居助手。回复简洁、内敛。"

    @observe(as_type="generation", name="fast_processing")
    async def process_fast(
        self,
        user_input: str,
        context: SystemContext
    ) -> Dict[str, Any]:
        """Process user input and generate response in one LLM call with Langfuse tracing"""

        # Step 1: Intent Analysis with trace
        self.logger.info(f"Starting intent analysis for: {user_input}")

        # Get context for analysis
        last_turn = context.get_conversation_context_for_llm(max_turns=1)
        last_device = context.last_device_action.get('device') if context.last_device_action else None
        familiarity = context.familiarity_score

        # Log familiarity check
        self.logger.info(f"User familiarity score: {familiarity}/100")

        prompt = f"""用户: "{user_input}"
{f"上次对话: {last_turn}" if last_turn else ""}
{f"最近设备: {last_device}" if last_device else ""}

熟悉度: {familiarity}/100 (需40+才能控制设备)

任务:
1. 分析用户意图
2. 制定执行计划
3. 以凌波丽身份回复

可用工具:
- familiarity_check: 检查用户权限
- device_control: 控制设备
- agora_tts: 生成语音

如需设备控制，在回复后加JSON:
{{"involves_hardware": true, "device": "lights", "action": "turn_on", "familiarity_check": "passed", "tools_needed": ["familiarity_check", "device_control", "agora_tts"]}}

简洁回复。"""

        try:
            # Use non-streaming for now to avoid async issues
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=self.config.anthropic.model,
                max_tokens=200,
                temperature=0.3,
                system=[{
                    "type": "text",
                    "text": self.character_prompt,
                    "cache_control": {"type": "ephemeral"}
                }],
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Parse response and extract JSON if present
            intent_analysis = None
            character_response = response_text

            # Simple JSON extraction
            if '{' in response_text and '}' in response_text:
                try:
                    # Find the JSON part
                    json_pattern = r'\{[^{}]*\}'
                    json_match = re.search(json_pattern, response_text)

                    if json_match:
                        json_str = json_match.group()
                        parsed_json = json.loads(json_str)

                        # Remove JSON from character response
                        character_response = response_text.replace(json_str, '').strip()

                        # Use parsed JSON as intent analysis
                        intent_analysis = parsed_json

                except Exception as e:
                    self.logger.warning(f"Failed to parse JSON: {e}")
                    self.logger.warning(f"Response was: {response_text}")

            # Default intent analysis if no JSON found
            if not intent_analysis:
                intent_analysis = {
                    "involves_hardware": False,
                    "device": None,
                    "action": None,
                    "familiarity_check": "not_needed",
                    "confidence": 0.5
                }

            # Log analysis results
            self.logger.info(f"Intent analysis: {intent_analysis}")
            if intent_analysis.get("involves_hardware"):
                familiarity_check = intent_analysis.get("familiarity_check", "unknown")
                self.logger.info(f"Hardware operation requested - Familiarity check: {familiarity_check}")

            # Update context
            context.add_conversation_turn(user_input, character_response)
            if intent_analysis.get("involves_hardware"):
                context.add_intent(intent_analysis)

            # Create execution plan from tools_needed
            tools_needed = intent_analysis.get("tools_needed", [])
            execution_plan = {
                "plan": [],
                "reasoning": f"Fast mode execution plan",
                "metadata": {
                    "fast_mode": True,
                    "tools_count": len(tools_needed)
                }
            }

            # Convert tools to plan steps
            for i, tool in enumerate(tools_needed, 1):
                if tool == "familiarity_check":
                    execution_plan["plan"].append({
                        "step": i,
                        "action": "familiarity_check",
                        "parameters": {"user_id": "default", "required_level": 40},
                        "reason": "检查用户设备控制权限"
                    })
                elif tool == "device_control" and intent_analysis.get("device"):
                    execution_plan["plan"].append({
                        "step": i,
                        "action": "device_control",
                        "parameters": {
                            "device": intent_analysis.get("device"),
                            "action": intent_analysis.get("action"),
                            "parameters": {}
                        },
                        "reason": "执行设备控制操作"
                    })
                elif tool == "agora_tts":
                    execution_plan["plan"].append({
                        "step": i,
                        "action": "agora_tts",
                        "parameters": {"text": character_response},
                        "reason": "生成语音输出"
                    })

            # Complete intent analysis for context
            complete_intent = {
                "involves_hardware": intent_analysis.get("involves_hardware", False),
                "device": intent_analysis.get("device"),
                "action": intent_analysis.get("action"),
                "parameters": {},
                "context_dependent": False,
                "reference_resolution": {
                    "has_reference": False,
                    "resolved_device": None,
                    "reference_word": None
                },
                "requires_status_query": False,
                "requires_memory": False,
                "memory_query": None,
                "confidence": intent_analysis.get("confidence", 0.5),
                "reasoning": f"Fast processing with planning: familiarity={familiarity}, tools={len(tools_needed)}",
                "familiarity_check": intent_analysis.get("familiarity_check", "not_needed")
            }

            # Log for Langfuse tracing
            self.logger.info(f"Fast processing completed - Hardware: {complete_intent['involves_hardware']}, Familiarity: {familiarity}, Check: {complete_intent['familiarity_check']}, Confidence: {complete_intent['confidence']}")

            return {
                "response": character_response,
                "intent_analysis": complete_intent,
                "execution_plan": execution_plan,
                "device_actions": [],
                "metadata": {
                    "fast_mode": True,
                    "model": self.config.anthropic.model,
                    "max_tokens": 200,
                    "processing_type": "intent_analysis_with_planning",
                    "familiarity_score": familiarity,
                    "familiarity_check": complete_intent["familiarity_check"],
                    "tools_planned": len(tools_needed)
                }
            }

        except Exception as e:
            self.logger.error(f"Fast processing error: {e}")
            return {
                "response": "系统处理中......",
                "intent_analysis": {"involves_hardware": False},
                "device_actions": []
            }