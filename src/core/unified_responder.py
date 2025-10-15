#!/usr/bin/env python3
"""
Unified Responder Component
Combines intent analysis and character response generation into a single LLM call
Optimized for speed by reducing API calls from 2 to 1
"""
import asyncio
import json
import logging
import re
from typing import Dict, Any, Optional

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


class UnifiedResponder:
    """Unified component that analyzes intent and generates character response in one LLM call"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.llm_client = create_llm_client(config)
        
        # Load prompts
        self.character_prompt = self._load_prompt_file('prompts/character.txt')
    
    def _load_prompt_file(self, filepath: str) -> str:
        """Load prompt from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Failed to load prompt file {filepath}: {e}")
            return "你是凌波丽，一个简洁内敛的AI助手。"
    
    def _get_familiarity_stage(self, familiarity_score: int) -> str:
        """Get familiarity stage description"""
        if familiarity_score < 30:
            return "初期（低熟悉度）"
        elif familiarity_score < 60:
            return "中期（中等熟悉度）"
        else:
            return "深入期（高熟悉度）"
    
    def _build_unified_system_prompt(
        self,
        context: SystemContext,
        device_states: Optional[str] = None
    ) -> str:
        """Build unified system prompt that includes both intent analysis and character response"""
        
        familiarity_stage = self._get_familiarity_stage(context.familiarity_score)
        
        # Base character prompt
        base_prompt = self.character_prompt
        
        # Add current context
        context_info = f"""

当前状态：
- 互动阶段: {familiarity_stage}
- 熟悉度分数: {context.familiarity_score}/100 (这决定了你是否愿意执行设备控制)
- 对话氛围: {context.conversation_tone}
{f"- 环境状态: {device_states}" if device_states else ""}

重要提醒：
1. 你的回应态度和是否执行设备控制完全取决于熟悉度分数
2. 低熟悉度(<30): 对陌生人保持距离，拒绝大部分设备控制
3. 中等熟悉度(30-60): 对认识的人选择性执行基础请求
4. 高熟悉度(>60): 对信任的人愿意执行大部分合理请求

输出格式要求：
你需要返回JSON格式，包含两部分：
1. intent: 意图分析结果
2. response: 你的角色回复

JSON格式:
{{
    "intent": {{
        "involves_hardware": true/false,
        "device": "lights/tv/air_conditioner/speaker/curtains/null",
        "action": "turn_on/turn_off/set_brightness/etc/null",
        "parameters": {{}},
        "confidence": 0.0-1.0,
        "familiarity_check": "passed"/"insufficient"/"not_required"
    }},
    "response": "你以凌波丽身份的回复文本"
}}

关键规则：
- 如果用户请求设备控制，根据熟悉度决定是否执行
- 熟悉度不足时，在response中礼貌拒绝，intent.familiarity_check设为"insufficient"
- 熟悉度充足时，在response中简洁确认，intent.familiarity_check设为"passed"
- 普通对话时，intent.involves_hardware设为false，intent.familiarity_check设为"not_required"
"""
        
        return base_prompt + context_info
    
    def _build_user_prompt(
        self,
        user_input: str,
        context: SystemContext
    ) -> str:
        """Build user prompt with conversation context"""
        
        # Get recent conversation
        max_turns = self.config.system.max_conversation_turns
        conversation_context = context.get_conversation_context_for_llm(max_turns=max_turns)
        
        prompt_parts = []
        
        # Add conversation history if available
        if conversation_context:
            prompt_parts.append(f"最近对话历史:\n{conversation_context}\n")
        
        # Add last device action for context resolution
        if context.last_device_action:
            prompt_parts.append(f"上次设备操作: {context.last_device_action.get('device')}\n")
        
        # Add current user input
        prompt_parts.append(f"当前用户输入: \"{user_input}\"\n")
        
        # Add instruction
        prompt_parts.append("""
请分析用户意图并生成你的回应。记住：
1. 如果涉及设备控制，先判断熟悉度是否足够
2. 用你独特的凌波丽式语言风格回应
3. 保持简洁，不要长篇大论
4. 返回完整的JSON格式
""")
        
        return "\n".join(prompt_parts)
    
    @observe(as_type="generation", name="unified_response")
    async def process_and_respond(
        self,
        user_input: str,
        context: SystemContext
    ) -> Dict[str, Any]:
        """
        Process user input and generate response in a single LLM call
        Returns: {
            "intent": {...},
            "response": "...",
            "success": bool,
            "error": str (optional)
        }
        """
        
        try:
            # Get device context
            device_states = context.get_device_context_for_llm()
            
            # Build prompts
            system_prompt = self._build_unified_system_prompt(context, device_states)
            user_prompt = self._build_user_prompt(user_input, context)
            
            # Single LLM call with full conversation history
            history_messages = context.get_conversation_messages_for_llm(
                max_turns=self.config.system.max_conversation_turns
            )
            # Append current turn user message at the end
            messages = history_messages + [{"role": "user", "content": user_prompt}]
            
            self.logger.info(f"🚀 Unified processing (1 API call) - Familiarity: {context.familiarity_score}/100")
            
            response_text = await self.llm_client.generate(
                system_prompt=system_prompt,
                messages=messages,
                max_tokens=self.config.gemini.max_tokens,  # use config (e.g., 10k)
                temperature=0.4  # Balanced for both analysis and creativity
            )
            
            # Parse JSON response
            try:
                # Extract JSON from response
                if response_text.startswith('{') and response_text.endswith('}'):
                    result = json.loads(response_text)
                else:
                    # Find JSON block
                    json_match = re.search(r'\{[\s\S]*\}', response_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group()
                        # Clean up common JSON issues
                        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
                        result = json.loads(json_text)
                    else:
                        raise ValueError("No valid JSON found in response")
                
                # Validate result structure
                if "intent" not in result or "response" not in result:
                    raise ValueError("Missing required fields: intent or response")
                
                # Add intent to context
                context.add_intent(result["intent"])
                
                # Log success
                self.logger.info(f"✅ Unified response generated - Hardware: {result['intent'].get('involves_hardware')}, Familiarity: {result['intent'].get('familiarity_check')}")
                
                return {
                    "intent": result["intent"],
                    "response": result["response"],
                    "success": True
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"JSON parsing failed: {e}, response: {response_text}")
                
                # Fallback: try to extract intent and response separately
                intent = self._extract_intent_fallback(response_text, context)
                response = self._extract_response_fallback(response_text, context)
                
                return {
                    "intent": intent,
                    "response": response,
                    "success": True,
                    "warning": "Used fallback parsing"
                }
        
        except Exception as e:
            self.logger.error(f"Unified responder error: {e}")
            
            # Return error response in character
            error_response = self._get_error_response(e, context)
            
            return {
                "intent": {
                    "involves_hardware": False,
                    "device": None,
                    "action": None,
                    "parameters": {},
                    "confidence": 0.0,
                    "familiarity_check": "not_required"
                },
                "response": error_response,
                "success": False,
                "error": str(e)
            }
    
    def _extract_intent_fallback(
        self,
        response_text: str,
        context: SystemContext
    ) -> Dict[str, Any]:
        """Fallback intent extraction from malformed response"""
        
        # Simple pattern matching
        involves_hardware = any(word in response_text.lower() 
                               for word in ['device', 'light', 'tv', 'air', 'speaker', 'curtain', '设备', '灯', '电视', '空调', '音响', '窗帘'])
        
        device_match = re.search(r'(lights?|tv|air_conditioner|speaker|curtains|灯|电视|空调|音响|窗帘)', 
                                response_text, re.IGNORECASE)
        device = device_match.group(1) if device_match else None
        
        return {
            "involves_hardware": involves_hardware,
            "device": device,
            "action": None,
            "parameters": {},
            "confidence": 0.3,
            "familiarity_check": "not_required"
        }
    
    def _extract_response_fallback(
        self,
        response_text: str,
        context: SystemContext
    ) -> str:
        """Fallback response extraction from malformed response"""
        
        # Try to find response field value
        response_match = re.search(r'"response"\s*:\s*"([^"]*)"', response_text)
        if response_match:
            return response_match.group(1)
        
        # Use raw text as response
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('{') and not line.startswith('"intent"'):
                return line
        
        # Ultimate fallback
        return "......出了点问题。"
    
    def _get_error_response(self, error: Exception, context: SystemContext) -> str:
        """Get character-appropriate error response"""
        if context.familiarity_score < 30:
            return "......出现了问题。"
        elif context.familiarity_score < 60:
            return "......系统出错了。稍等。"
        else:
            return "......出了点问题。让我看看......"


# Convenience function for backward compatibility
async def analyze_and_respond(
    user_input: str,
    context: SystemContext,
    config: Config
) -> Dict[str, Any]:
    """
    Convenience function for unified intent analysis and response generation
    """
    responder = UnifiedResponder(config)
    return await responder.process_and_respond(user_input, context)

