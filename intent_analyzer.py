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

from config import Config
from context_manager import SystemContext


class IntentAnalyzer:
    """Analyzes user intent from natural language input using LLM"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.claude_client = anthropic.Anthropic(
            api_key=config.anthropic.api_key,
            max_retries=3,
            timeout=30.0
        )
        
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
        """Analyze user intent using LLM with full context awareness"""
        
        # Build context-aware prompt
        conversation_context = context.get_conversation_context_for_llm(max_turns=5)
        device_context = context.get_device_context_for_llm()
        
        # Let LLM detect and handle reference words contextually
        
        analysis_prompt = f"""
        作为智能家居系统的意图分析器，请分析用户输入并理解其真实意图。
        不要使用关键词匹配，而是理解语义和上下文。
        
        当前用户输入: "{user_input}"
        
        对话历史:
        {conversation_context if conversation_context else "无历史对话"}
        
        {device_context}
        
        用户熟悉度: {context.familiarity_score}/100
        对话基调: {context.conversation_tone}
        
        上一次设备操作: {json.dumps(context.last_device_action, ensure_ascii=False) if context.last_device_action else "无"}
        
        可用设备类型:
        - lights (灯/灯光/照明)
        - tv (电视/电视机/TV)
        - air_conditioner (空调/冷气/暖气)
        - speaker (音响/音箱/扬声器)
        - curtains (窗帘/窗户/遮光帘)
        
        重要提示:
        1. 如果用户说"它"、"那个"等指代词，需要从上下文推断具体设备
        2. 理解隐含意图，如"好热"可能意味着想开空调
        3. 区分设备控制、状态查询和普通对话
        4. 考虑上下文连续性，如连续的设备操作请求
        
        返回JSON格式:
        {{
            "involves_hardware": boolean,  // 是否涉及硬件操作
            "device": "具体设备ID或null",  // 如lights, tv等
            "action": "操作类型或null",  // 如turn_on, turn_off, set_brightness等
            "parameters": {{  // 操作参数
                "brightness": number或null,  // 亮度0-100
                "temperature": number或null,  // 温度16-30
                "volume": number或null  // 音量0-100
            }},
            "context_dependent": boolean,  // 是否依赖上下文理解
            "reference_resolution": {{  // 指代词解析
                "has_reference": boolean,
                "resolved_device": "设备ID或null",
                "reference_word": "指代词或null"
            }},
            "requires_status_query": boolean,  // 是否需要查询设备状态
            "requires_memory": boolean,  // 是否需要记忆检索
            "memory_query": "记忆查询内容或null",
            "confidence": 0.0-1.0,  // 置信度
            "reasoning": "分析推理过程"  // 解释为什么这样判断
        }}
        
        只返回JSON，不要任何额外文字。
        """
        
        try:
            # Use prompt caching for system prompt to save tokens
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=self.config.anthropic.model,
                max_tokens=800,
                temperature=0.3,  # Lower temperature for more consistent analysis
                system=[{
                    "type": "text",
                    "text": self.system_prompt,
                    "cache_control": {"type": "ephemeral"}  # Cache the system prompt
                }],
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            response_text = response.content[0].text.strip()
            
            # Extract JSON
            if response_text.startswith('{') and response_text.endswith('}'):
                intent_json = json.loads(response_text)
            else:
                # Find JSON part
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    intent_json = json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in response")
            
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
