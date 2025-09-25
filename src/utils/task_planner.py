#!/usr/bin/env python3
"""
Task Planner Component
Central orchestration agent that analyzes user intent and coordinates tool calls
"""
import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

# Try to import Langfuse, fall back gracefully
try:
    from langfuse import observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from .config import Config
from ..services.database_service import DatabaseService
from ..models.database import ConversationContext


class TaskPlanner:
    """Central orchestration agent for the smart home system"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize core services
        self.db_service = DatabaseService(config)
        
        # Lazy-load other components to avoid circular imports
        self._intent_analyzer = None
        self._device_controller = None
        self._character_system = None
        
        # In-memory conversation cache
        self.active_conversations: Dict[str, ConversationContext] = {}
    
    @property
    def intent_analyzer(self):
        """Lazy-load intent analyzer"""
        if self._intent_analyzer is None:
            from ..core.intent_analyzer import IntentAnalyzer
            self._intent_analyzer = IntentAnalyzer(self.config)
        return self._intent_analyzer
    
    @property
    def device_controller(self):
        """Lazy-load device controller"""
        if self._device_controller is None:
            from ..core.device_controller import DeviceController
            self._device_controller = DeviceController(self.config)
        return self._device_controller
    
    @property
    def character_system(self):
        """Lazy-load character system"""
        if self._character_system is None:
            from ..core.character_system import CharacterSystem
            self._character_system = CharacterSystem(self.config)
        return self._character_system
    
    def get_or_create_conversation(self, user_id: str, conversation_id: str = None) -> ConversationContext:
        """Get existing conversation or create new one"""
        if conversation_id and conversation_id in self.active_conversations:
            ctx = self.active_conversations[conversation_id]
            ctx.update_activity()
            return ctx
        
        # Create new conversation
        user = self.db_service.get_or_create_user(user_id)
        
        ctx = ConversationContext(
            conversation_id=conversation_id or str(uuid.uuid4()),
            user_id=user_id,
            familiarity_score=user.familiarity_score,
            tone=self._determine_tone(user.familiarity_score)
        )
        
        self.active_conversations[ctx.conversation_id] = ctx
        return ctx
    
    def _determine_tone(self, familiarity_score: int) -> str:
        """Determine conversation tone based on familiarity"""
        if familiarity_score <= 30:
            return "formal"
        elif familiarity_score <= 60:
            return "polite"
        elif familiarity_score <= 80:
            return "casual"
        else:
            return "intimate"
    
    @observe(as_type="generation", name="task_planner_main")
    async def process_request(self, user_input: str, user_id: str, conversation_id: str = None) -> tuple[str, str]:
        """Main orchestration logic"""
        # Validate input
        if not user_input or not user_input.strip():
            return "请输入您的问题或指令。", conversation_id or str(uuid.uuid4())
        
        # Get conversation context
        conversation_ctx = self.get_or_create_conversation(user_id, conversation_id)
        
        try:
            # Step 1: Analyze user intent
            intent = await self.intent_analyzer.analyze_intent(
                user_input, 
                conversation_ctx.familiarity_score, 
                conversation_ctx
            )
            
            # Step 2: Execute based on intent
            if intent["requires_hardware"]:
                # Device control flow - let Device Controller analyze and execute
                device_result = await self.device_controller.analyze_and_control(
                    user_input=user_input,
                    conversation_ctx=conversation_ctx,
                    is_status_query=False
                )
                
                response = await self.character_system.generate_response(
                    message=user_input,
                    tone=conversation_ctx.tone,
                    context=f"设备控制结果: {json.dumps(device_result, ensure_ascii=False)}",
                    conversation_context=conversation_ctx,
                    response_type="device_control"
                )
                
            elif intent["requires_status"]:
                # Status query flow - let Device Controller analyze and query
                device_result = await self.device_controller.analyze_and_control(
                    user_input=user_input,
                    conversation_ctx=conversation_ctx,
                    is_status_query=True
                )
                
                response = await self.character_system.generate_response(
                    message=user_input,
                    tone=conversation_ctx.tone,
                    context=f"设备状态查询结果: {json.dumps(device_result, ensure_ascii=False)}",
                    conversation_context=conversation_ctx,
                    response_type="device_status"
                )
                
            elif intent["requires_memory"]:
                # Memory retrieval flow
                memories = await self._retrieve_memory(
                    intent["memory_query"], 
                    user_id
                )
                
                response = await self.character_system.generate_response(
                    message=user_input,
                    tone=conversation_ctx.tone,
                    context=f"相关记忆: {json.dumps(memories, ensure_ascii=False)}",
                    conversation_context=conversation_ctx,
                    response_type="general"
                )
                
            else:
                # Pure conversational flow
                response = await self.character_system.generate_response(
                    message=user_input,
                    tone=conversation_ctx.tone,
                    context="",
                    conversation_context=conversation_ctx,
                    response_type="general"
                )
            
            # Save to database
            self.db_service.save_message(
                conversation_id=conversation_ctx.conversation_id,
                user_input=user_input,
                assistant_response=response,
                tone_used=conversation_ctx.tone,
                intent_detected=intent
            )
            
            return response, conversation_ctx.conversation_id
            
        except Exception as e:
            self.logger.error(f"Task planner error: {e}")
            
            # Fallback response
            response = await self.character_system.generate_response(
                message="处理请求时遇到问题",
                tone=conversation_ctx.tone,
                context=f"错误信息: {str(e)}",
                conversation_context=conversation_ctx,
                response_type="error"
            )
            
            return response, conversation_ctx.conversation_id
    
    async def _retrieve_memory(self, query: str, user_id: str) -> list:
        """Retrieve user memories"""
        memories = self.db_service.search_user_memories(user_id, query, limit=5)
        return [memory.to_dict() for memory in memories]
