#!/usr/bin/env python3
"""
Character System Component
Generates contextually-aware responses in the personality of 凌波丽 (Rei Ayanami)
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

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


class CharacterSystem:
    """Handles character-based response generation with full context awareness"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.claude_client = anthropic.Anthropic(
            api_key=config.anthropic.api_key,
            max_retries=3,
            timeout=30.0
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
            return self._get_default_character_prompt()
    
    def _get_default_character_prompt(self) -> str:
        """Default character prompt if file not found"""
        return """
你是凌波丽（Rei Ayanami），来自《新世纪福音战士》的角色。
保持以下性格特征：
- 说话简洁、直接，很少使用多余的词汇
- 情感表达内敛，语气平静
- 偶尔会表现出微妙的关心
- 使用"......"表示停顿或沉默
- 对技术和任务保持专注
"""
    
    @observe(as_type="generation", name="character_response")
    async def generate_response(
        self,
        context: SystemContext,
        response_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate contextually-aware character response"""

        # Build optimized prompt based on context
        character_prompt = self._build_character_prompt(context, response_data)

        try:
            # Use prompt caching for the character system prompt to save tokens
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=self.config.anthropic.model,
                max_tokens=150,  # Reduced from 1000 for faster responses
                temperature=0.5,  # Lower temperature for faster generation
                system=[{
                    "type": "text",
                    "text": character_prompt["system"],
                    "cache_control": {"type": "ephemeral"}  # Cache the character system prompt
                }],
                messages=[{"role": "user", "content": character_prompt["user_content"]}]
            )
            
            character_response = response.content[0].text
            
            # Update context with response
            context.add_conversation_turn(
                user_msg=context.user_input,
                assistant_msg=character_response
            )
            
            # Log character response metadata (captured by @observe decorator)  
            response_type = self._determine_response_type(context, response_data)
            self.logger.debug(f"Character response - Type: {response_type}, Familiarity: {context.familiarity_score}, Tone: {context.conversation_tone}")
            
            self.logger.debug(f"Character response generated: {character_response[:100]}...")
            return character_response
            
        except Exception as e:
            self.logger.error(f"Character system error: {e}")
            return self._get_error_response(e, context)
    
    def _build_character_prompt(
        self,
        context: SystemContext,
        response_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Build optimized character prompt with minimal context"""

        # Get only recent conversation (reduced from 5 to 1)
        conv_history = context.get_conversation_context_for_llm(max_turns=1)

        # Simplified system prompt
        system_prompt = f"""
你是凌波丽。简洁、平静、内敛。
使用"......"表示停顿。
熟悉度:{context.familiarity_score}/100
7. 避免使用（）描述动作或表情
"""
        
        user_content = f"""
用户输入: {context.user_input}

请以凌波丽的身份回应，考虑以上所有上下文信息。
"""
        
        return {
            "system": system_prompt,
            "user_content": user_content
        }
    
    def _determine_response_type(
        self,
        context: SystemContext,
        response_data: Optional[Dict[str, Any]]
    ) -> str:
        """Determine the type of response needed"""
        
        if not response_data:
            return "conversation"
        
        if response_data.get("error"):
            return "error"
        
        if response_data.get("action_type") == "control":
            return "device_control"
        
        if response_data.get("action_type") == "query":
            return "device_status"
        
        if response_data.get("requires_confirmation"):
            return "confirmation"
        
        if response_data.get("insufficient_familiarity"):
            return "rejection"
        
        return "general"
    
    def _get_tone_guidance(self, familiarity_score: int, conversation_tone: str) -> str:
        """Get tone guidance based on familiarity"""
        
        if familiarity_score < 30:
            return """
保持礼貌但疏离的态度：
- 使用敬语和正式称呼
- 回复简短且功能性
- 几乎不表露个人情感
- 保持专业距离
"""
        elif familiarity_score < 60:
            return """
逐渐放松但仍保持一定距离：
- 偶尔使用较为随意的语言
- 可以有简单的情感表达
- 开始记住用户的偏好
- 适度关心用户状态
"""
        elif familiarity_score < 80:
            return """
表现出信任和舒适感：
- 语言更加自然随意
- 会主动询问用户感受
- 记得之前的对话内容
- 表现出细微的关心
"""
        else:
            return """
展现深层的连接和理解：
- 语言亲密自然
- 能理解用户的隐含意图
- 主动关心和提供建议
- 偶尔表露真实情感
- 可以开一些温和的玩笑
"""
    
    def _build_specific_context(
        self,
        response_type: str,
        context: SystemContext,
        response_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build specific context based on response type"""
        
        if response_type == "device_control":
            device_info = response_data.get("execution", {})
            return f"""
设备控制结果：
- 设备: {device_info.get('device_name', '未知设备')}
- 操作: {device_info.get('message', '操作完成')}
- 成功: {'是' if device_info.get('success') else '否'}

请确认设备操作结果，语气保持平静。
"""
        
        elif response_type == "device_status":
            query_result = response_data.get("query_result", {})
            return f"""
设备状态查询结果：
{query_result.get('summary', '无设备状态信息')}

简洁地报告设备状态，必要时询问是否需要调整。
"""
        
        elif response_type == "error":
            error_msg = response_data.get("error", "未知错误")
            return f"""
系统错误：
{error_msg}

以凌波丽的方式表达困惑或歉意，保持冷静。
"""
        
        elif response_type == "rejection":
            return f"""
用户熟悉度不足，无法执行请求。
需要的熟悉度: {response_data.get('required_score', 50)}
当前熟悉度: {context.familiarity_score}

委婉地拒绝请求，暗示需要更多互动来建立信任。
"""
        
        elif response_type == "confirmation":
            return f"""
需要用户确认的操作：
{response_data.get('message', '')}

询问用户是否确认执行该操作。
"""
        
        else:
            # General conversation
            device_states = context.get_device_context_for_llm()
            return f"""
当前环境状态：
{device_states}

这是一般对话，根据用户输入自然回应。
"""
    
    def _get_error_response(self, error: Exception, context: SystemContext) -> str:
        """Get character-appropriate error response"""
        error_message = str(error).lower()
        
        if context.familiarity_score < 30:
            # Formal error responses
            if "529" in str(error) or "overloaded" in error_message:
                return "系统繁忙。请稍后再试。"
            elif "401" in str(error) or "authentication" in error_message:
                return "认证失败。无法连接系统。"
            elif "timeout" in error_message:
                return "响应超时。请重试。"
            else:
                return "系统错误。"
        else:
            # More personal error responses for higher familiarity
            if "529" in str(error) or "overloaded" in error_message:
                return "......系统很忙。稍等一下好吗？"
            elif "401" in str(error) or "authentication" in error_message:
                return "......连接出了问题。我在想办法。"
            elif "timeout" in error_message:
                return "......太慢了。要不要再试一次？"
            else:
                return "......出了点问题。让我看看......"
    
    @observe(as_type="generation", name="generate_idle_response")
    async def generate_idle_response(self, context: SystemContext) -> str:
        """Generate idle/ambient responses based on context"""
        
        # Check time of day and device states
        current_hour = datetime.now().hour
        device_states = context.device_states
        
        idle_prompt = f"""
作为凌波丽，生成一个环境感知的闲聊。

当前时间: {current_hour}点
熟悉度: {context.familiarity_score}
最后互动: {context.last_response if context.last_response else '无'}
设备状态数: {len(device_states)}

根据时间和环境状态，生成适合的闲聊内容。
可以是：
- 对时间的观察（深夜、清晨等）
- 对环境的感知（灯光、温度等）
- 简单的关心（如果熟悉度高）
- 沉默的表达（"......"）

保持凌波丽的性格，简短而有氛围感。
"""
        
        try:
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=self.config.anthropic.model,
                max_tokens=100,
                temperature=0.8,
                system=self.character_prompt,
                messages=[{"role": "user", "content": idle_prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            self.logger.error(f"Idle response generation error: {e}")
            return "......"