#!/usr/bin/env python3
"""
Intent Analyzer Component
Analyzes user input to determine intent and required actions using LLM
"""
import asyncio
import json
import logging
import re
from typing import Dict, Any, Optional

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
from ..utils.llm_client import create_llm_client
from .context_manager import SystemContext


class IntentAnalyzer:
    """Analyzes user intent from natural language input using LLM"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.llm_client = create_llm_client(config)
        
        # Load system prompt
        self.system_prompt = self._load_prompt_file('prompts/intent_analyzer.txt')
    
    def _load_prompt_file(self, filepath: str) -> str:
        """Load prompt from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Failed to load prompt file {filepath}: {e}")
            return "你是一个智能意图分析系统，理解用户输入并返回JSON格式结果。"
    
    @observe(as_type="generation", name="intent_analysis")
    async def analyze_intent(
        self,
        user_input: str,
        context: SystemContext
    ) -> Dict[str, Any]:
        """Analyze user intent using LLM with optimized context"""

        # Include recent conversation for context
        max_turns = self.config.system.max_conversation_turns
        conversation_context = context.get_conversation_context_for_llm(max_turns=max_turns)

        # Enhanced prompt with better context understanding
        analysis_prompt = f"""
当前用户输入: "{user_input}"

{f"最近对话历史: {conversation_context}" if conversation_context else ""}
{f"上次设备操作: {context.last_device_action.get('device')}" if context.last_device_action else ""}

分析要求：
1. 理解上下文关联：如果用户说"是命令"、"执行"、"好的"等确认词，检查前面是否有未执行的设备操作请求
2. 指代词解析：如"它"、"那个"等需要从对话历史中找到对应的设备
3. 隐含意图：如"好热"暗示开空调，"太亮了"暗示调暗灯光

返回JSON格式：
{{
    "involves_hardware": bool,
    "device": "lights/tv/air_conditioner/speaker/curtains/null",
    "action": "turn_on/turn_off/set_brightness/null",
    "parameters": {{}},
    "confidence": 0.0-1.0,
    "context_reference": "描述如何理解上下文"
}}
"""
        
        try:
            # Generate intent analysis using LLM client
            system_prompt_text = "你是智能家居意图分析器。分析用户输入，返回JSON格式的设备控制意图。"
            messages = [{"role": "user", "content": analysis_prompt}]
            
            response_text = await self.llm_client.generate(
                system_prompt=system_prompt_text,
                messages=messages,
                max_tokens=200,  # Reduced from 800
                temperature=0.1  # Lower temperature for faster, more consistent analysis
            )
            
            # Extract JSON with better error handling
            try:
                if response_text.startswith('{') and response_text.endswith('}'):
                    intent_json = json.loads(response_text)
                else:
                    # Find JSON part using more robust pattern
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group()
                        # Clean up common JSON formatting issues
                        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)  # Remove trailing commas
                        json_text = re.sub(r'([{,]\s*)"?(\w+)"?\s*:', r'\1"\2":', json_text)  # Quote keys
                        intent_json = json.loads(json_text)
                    else:
                        raise ValueError("No valid JSON found in response")
            except json.JSONDecodeError as json_error:
                self.logger.warning(f"JSON parsing failed: {json_error}, response: {response_text}")
                # Try to extract basic information manually
                involves_hardware = any(word in response_text.lower() for word in ['true', '是', '硬件', 'hardware'])
                device_matches = re.search(r'(lights?|tv|air_conditioner|speaker|curtains)', response_text.lower())
                device = device_matches.group(1) if device_matches else None

                intent_json = {
                    "involves_hardware": involves_hardware,
                    "device": device,
                    "action": None,
                    "parameters": {},
                    "confidence": 0.3,
                    "context_reference": "JSON解析失败，使用简单文本分析"
                }
            
            # Process reference resolution if needed
            if intent_json.get("reference_resolution", {}).get("has_reference"):
                resolved_device = self._resolve_device_reference(context, intent_json)
                if resolved_device:
                    intent_json["device"] = resolved_device
                    intent_json["reference_resolution"]["resolved_device"] = resolved_device
            
            # Store intent in context
            context.add_intent(intent_json)
            
            # Logging intent analysis results (Langfuse will capture this via @observe decorator)
            self.logger.debug(f"Intent analysis - Confidence: {intent_json.get('confidence', 0.0)}, Hardware: {intent_json.get('involves_hardware', False)}")
            
            self.logger.debug(f"Intent analysis result: {json.dumps(intent_json, ensure_ascii=False)}")
            return intent_json
            
        except Exception as e:
            self.logger.error(f"Intent analysis error: {e}")
            
            # Try simpler LLM approach first for API errors
            if "529" in str(e) or "overloaded" in str(e).lower() or "rate_limit" in str(e).lower():
                try:
                    # Attempt with minimal context and lower token limit
                    simplified_prompt = f"""
                    分析用户输入的意图: "{user_input}"
                    
                    返回JSON格式:
                    {{
                        "involves_hardware": boolean,
                        "device": "设备类型或null",
                        "action": "操作或null", 
                        "confidence": 0.0-1.0,
                        "reasoning": "简要分析"
                    }}
                    """
                    
                    response = await asyncio.to_thread(
                        self.claude_client.messages.create,
                        model="claude-3-haiku-20240307",  # Use faster, cheaper model
                        max_tokens=200,
                        temperature=0.1,
                        system=[{
                            "type": "text",
                            "text": "你是意图分析助手，分析用户输入并返回JSON。",
                            "cache_control": {"type": "ephemeral"}
                        }],
                        messages=[{"role": "user", "content": simplified_prompt}]
                    )
                    
                    response_text = response.content[0].text.strip()
                    if response_text.startswith('{') and response_text.endswith('}'):
                        simple_result = json.loads(response_text)
                        # Expand to full format
                        return {
                            "involves_hardware": simple_result.get("involves_hardware", False),
                            "device": simple_result.get("device"),
                            "action": simple_result.get("action"),
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
                            "confidence": simple_result.get("confidence", 0.3),
                            "reasoning": f"Simplified analysis: {simple_result.get('reasoning', 'Basic LLM analysis')}"
                        }
                except Exception as fallback_e:
                    self.logger.error(f"Simplified LLM fallback also failed: {fallback_e}")
            
            # Final fallback - minimal analysis
            return await self._enhanced_fallback_analysis(user_input, context)
    
    def _resolve_device_reference(
        self,
        context: SystemContext,
        intent: Dict[str, Any]
    ) -> Optional[str]:
        """Resolve device references from context"""
        reference_word = intent.get("reference_resolution", {}).get("reference_word")
        
        if reference_word:
            # Try to resolve from context
            resolved = context.resolve_reference(reference_word)
            if resolved:
                self.logger.info(f"Resolved reference '{reference_word}' to '{resolved}'")
                return resolved
                
        return None
    
    async def _enhanced_fallback_analysis(
        self,
        user_input: str,
        context: SystemContext
    ) -> Dict[str, Any]:
        """Fallback when LLM API is unavailable - returns minimal analysis"""
        self.logger.warning("LLM API unavailable, using minimal fallback analysis")
        
        # Check for basic reference words in context
        reference_words = ["它", "那个", "这个", "刚才的", "之前的"]
        has_reference = any(ref in user_input for ref in reference_words)
        reference_word = next((ref for ref in reference_words if ref in user_input), None)
        
        # Try to resolve reference from context if available
        resolved_device = None
        if has_reference and reference_word:
            resolved_device = context.resolve_reference(reference_word)
        
        # Return conservative analysis - let other components handle the complexity
        return {
            "involves_hardware": False,  # Conservative - assume no hardware control without LLM
            "device": resolved_device,   # Only if resolved from context
            "action": None,
            "parameters": {},
            "context_dependent": has_reference,
            "reference_resolution": {
                "has_reference": has_reference,
                "resolved_device": resolved_device,
                "reference_word": reference_word
            },
            "requires_status_query": False,
            "requires_memory": False,
            "memory_query": None,
            "confidence": 0.1,  # Very low confidence without LLM analysis
            "reasoning": "LLM unavailable - minimal fallback analysis, recommend retry"
        }
