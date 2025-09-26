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
        """Default character prompt if file not found - minimal fallback"""
        return "你是凌波丽，一个简洁内敛的AI助手。"
    
    @observe(as_type="generation", name="character_response")
    async def generate_response(
        self,
        context: SystemContext,
        response_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate contextually-aware character response"""

        try:
            # Get conversation messages in standard format (includes current user input)
            max_turns = self.config.system.max_conversation_turns
            conversation_messages = context.get_conversation_messages_for_llm(max_turns=max_turns)
            
            # Build system prompt with context
            system_prompt = self._build_system_prompt(context, response_data)
            
            # Prepare messages for LLM
            messages = []
            
            # Add conversation history
            if conversation_messages:
                messages.extend(conversation_messages)
            
            # Add current context if no history or if we need to add context
            if not conversation_messages or response_data:
                context_content = self._build_context_content(context, response_data)
                if context_content:
                    messages.append({"role": "user", "content": context_content})
            
            # Use prompt caching for the character system prompt to save tokens
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=self.config.anthropic.model,
                max_tokens=150,  # Reduced from 1000 for faster responses
                temperature=0.5,  # Lower temperature for faster generation
                system=[{
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}  # Cache the character system prompt
                }],
                messages=messages
            )
            
            character_response = response.content[0].text
            
            # Log character response metadata (captured by @observe decorator)  
            response_type = self._determine_response_type(context, response_data)
            self.logger.debug(f"Character response - Type: {response_type}, Familiarity: {context.familiarity_score}, Tone: {context.conversation_tone}")
            
            self.logger.debug(f"Character response generated: {character_response[:100]}...")
            return character_response
            
        except Exception as e:
            self.logger.error(f"Character system error: {e}")
            return self._get_error_response(e, context)
    
    def _build_system_prompt(
        self,
        context: SystemContext,
        response_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build system prompt for character based on loaded prompt file"""
        
        # Start with the loaded character prompt from file
        base_prompt = self.character_prompt
        
        # Add current context information (without exposing familiarity score)
        familiarity_stage = self._get_familiarity_stage(context.familiarity_score)
        context_info = f"""

当前状态：
- 互动阶段: {familiarity_stage}
- 对话氛围: {context.conversation_tone}
"""
        
        # Add specific context if needed
        response_type = self._determine_response_type(context, response_data)
        specific_context = self._build_specific_context(response_type, context, response_data)
        
        if specific_context:
            context_info += f"\n{specific_context}"
        
        # Combine base prompt with context
        system_prompt = base_prompt + context_info
        
        return system_prompt
    
    def _build_context_content(
        self,
        context: SystemContext,
        response_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Build additional context content if needed"""
        
        if not response_data:
            return None
            
        # Only add context for specific response types that need extra information
        response_type = self._determine_response_type(context, response_data)
        
        if response_type in ["device_control", "device_status", "error", "confirmation", "rejection"]:
            return f"系统信息: {response_data}"
            
        return None
    
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
    
    def _get_familiarity_stage(self, familiarity_score: int) -> str:
        """Get familiarity stage description"""
        if familiarity_score < 30:
            return "初期（低熟悉度）"
        elif familiarity_score < 60:
            return "中期（中等熟悉度）"
        else:
            return "深入期（高熟悉度）"
    
    def _build_specific_context(
        self,
        response_type: str,
        context: SystemContext,
        response_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build specific context based on response type"""
        
        context_parts = []
        
        # Add familiarity stage
        familiarity_stage = self._get_familiarity_stage(context.familiarity_score)
        context_parts.append(f"当前互动阶段: {familiarity_stage}")
        
        # Add response-specific context
        if response_type == "device_control" and response_data:
            device_info = response_data.get("execution", {})
            context_parts.append(f"设备控制: {device_info.get('device_name', '设备')} - {device_info.get('message', '操作完成')}")
        
        elif response_type == "device_status" and response_data:
            query_result = response_data.get("query_result", {})
            context_parts.append(f"设备状态查询: {query_result.get('summary', '查询完成')}")
        
        elif response_type == "error" and response_data:
            error_msg = response_data.get("error", "系统错误")
            context_parts.append(f"系统状态: {error_msg}")
        
        elif response_type == "rejection" and response_data:
            context_parts.append("权限不足: 拒绝执行请求")
        
        elif response_type == "confirmation" and response_data:
            message = response_data.get('message', '需要确认')
            context_parts.append(f"等待确认: {message}")
        
        # Add device states for general context
        if response_type in ["general", "conversation"]:
            device_states = context.get_device_context_for_llm()
            if device_states and device_states != "暂无设备状态信息":
                context_parts.append(f"环境状态: {device_states}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _get_error_response(self, error: Exception, context: SystemContext) -> str:
        """Get character-appropriate error response"""
        # Simple fallback based on familiarity
        if context.familiarity_score < 30:
            return "......出现了问题。"
        else:
            return "......出了点问题。让我看看......"
    
    @observe(as_type="generation", name="generate_idle_response")
    async def generate_idle_response(self, context: SystemContext) -> str:
        """Generate idle/ambient responses based on context"""
        
        # Check time of day and device states
        current_hour = datetime.now().hour
        device_states = context.device_states
        familiarity_stage = self._get_familiarity_stage(context.familiarity_score)
        
        # Simple context information
        idle_context = f"""
环境感知闲聊请求

当前时间: {current_hour}点
互动阶段: {familiarity_stage}
设备状态数: {len(device_states)}
"""
        
        try:
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=self.config.anthropic.model,
                max_tokens=100,
                temperature=0.8,
                system=self.character_prompt,
                messages=[{"role": "user", "content": idle_context}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            self.logger.error(f"Idle response generation error: {e}")
            return "......"