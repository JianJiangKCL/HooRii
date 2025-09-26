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
from ..core.context_manager import SystemContext


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
        self.active_conversations: Dict[str, SystemContext] = {}

        # Load familiarity config
        self.familiarity_config = self._load_familiarity_config()
    
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

    def _load_familiarity_config(self) -> Dict[str, Any]:
        """Load familiarity configuration from file"""
        try:
            with open('config/familiarity_requirements.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load familiarity config: {e}")
            # Return defaults
            return {
                "tone_thresholds": {
                    "formal": 30,
                    "polite": 60,
                    "casual": 80,
                    "intimate": 100
                }
            }
    
    def get_or_create_conversation(self, user_id: str, conversation_id: str = None) -> tuple[SystemContext, str]:
        """Get existing conversation or create new one, returns (SystemContext, conversation_id)"""
        # If no conversation_id provided, try to find the most recent active conversation for this user
        if not conversation_id:
            try:
                # Look for recent conversation in database
                recent_conversations = self.db_service.get_recent_conversations_for_user(user_id, limit=1)
                if recent_conversations:
                    latest_conv = recent_conversations[0]
                    # Only continue recent conversations (within last 24 hours)
                    import datetime
                    time_diff = datetime.datetime.now() - latest_conv.last_activity
                    if time_diff.total_seconds() < 86400:  # 24 hours
                        conversation_id = latest_conv.id
                        self.logger.info(f"Continuing recent conversation {conversation_id} for user {user_id}")
            except Exception as e:
                self.logger.warning(f"Failed to find recent conversation for user {user_id}: {e}")

        conv_id = conversation_id or str(uuid.uuid4())

        if conv_id in self.active_conversations:
            ctx = self.active_conversations[conv_id]
            return ctx, conv_id

        # Create new conversation or load existing one from database
        user = self.db_service.get_or_create_user(user_id)

        # Read user attributes before they become detached
        user_familiarity = user.familiarity_score

        # Create or get conversation in database
        # We'll handle database conversation creation separately to avoid session issues
        try:
            db_conversation = self.db_service.get_or_create_conversation(user_id, conv_id)
            # Use the existing conv_id if successful
        except Exception as e:
            self.logger.warning(f"Database conversation creation failed: {e}")

        # Create SystemContext for compatibility with other components
        ctx = SystemContext(
            user_input="",
            familiarity_score=user_familiarity,
            conversation_tone=self._determine_tone(user_familiarity),
            session_id=conv_id
        )

        # If conversation_id was provided, try to load history from database
        if conversation_id:
            try:
                history = self.db_service.get_conversation_history(conversation_id, limit=50)
                if history:
                    self.logger.info(f"Loading {len(history)} messages from database for conversation {conversation_id}")

                    # Rebuild conversation history from database
                    for message in history:
                        if message.user_input:
                            ctx.conversation_history.append({
                                "role": "user",
                                "content": message.user_input,
                                "timestamp": message.timestamp.isoformat()
                            })
                        if message.assistant_response:
                            ctx.conversation_history.append({
                                "role": "assistant",
                                "content": message.assistant_response,
                                "timestamp": message.timestamp.isoformat()
                            })

                    # Update message count
                    ctx.message_count = len(ctx.conversation_history)

                    # Update familiarity based on conversation length (longer conversations = more familiar)
                    if len(history) > 5:  # If more than 5 exchanges, increase familiarity slightly
                        ctx.familiarity_score = min(100, user_familiarity + len(history) * 2)
                        ctx.conversation_tone = self._determine_tone(ctx.familiarity_score)

                    self.logger.info(f"Restored conversation context: {ctx.message_count} messages, familiarity: {ctx.familiarity_score}")
            except Exception as e:
                self.logger.warning(f"Failed to load conversation history for {conversation_id}: {e}")

        self.active_conversations[conv_id] = ctx
        return ctx, conv_id
    
    def _determine_tone(self, familiarity_score: int) -> str:
        """Determine conversation tone based on familiarity"""
        thresholds = self.familiarity_config.get("tone_thresholds", {})

        if familiarity_score <= thresholds.get("formal", 30):
            return "formal"
        elif familiarity_score <= thresholds.get("polite", 60):
            return "polite"
        elif familiarity_score <= thresholds.get("casual", 80):
            return "casual"
        else:
            return "intimate"
    
    @observe(as_type="generation", name="task_planner_main")
    async def process_request(self, user_input: str, user_id: str, conversation_id: str = None) -> tuple[str, str]:
        """Main orchestration logic with centralized context management"""
        # Validate input
        if not user_input or not user_input.strip():
            return "请输入您的问题或指令。", conversation_id or str(uuid.uuid4())

        # Get conversation context
        conversation_ctx, conv_id = self.get_or_create_conversation(user_id, conversation_id)
        conversation_ctx.user_input = user_input

        # Add user message to history BEFORE analyzing intent
        # This ensures intent analyzer sees the full conversation including current message
        conversation_ctx.add_user_message(user_input)

        try:
            # Step 1: Analyze user intent (with full conversation history)
            intent = await self.intent_analyzer.analyze_intent(
                user_input,
                conversation_ctx
            )
            
            # Step 2: Execute based on intent
            if intent.get("involves_hardware", False):
                # Device control flow - let Device Controller process
                device_result = await self.device_controller.process_device_intent(
                    intent=intent,
                    context=conversation_ctx
                )
                
                # Update context with device result
                conversation_ctx.current_intent.update({
                    "device_result": device_result
                })
                response = await self.character_system.generate_response(
                    context=conversation_ctx,
                    response_data={"device_result": device_result}
                )
                
            elif intent.get("requires_status", False):
                # Status query flow - let Device Controller process
                device_result = await self.device_controller.process_device_intent(
                    intent=intent,
                    context=conversation_ctx
                )
                
                # Update context with status result
                conversation_ctx.current_intent.update({
                    "status_result": device_result
                })
                response = await self.character_system.generate_response(
                    context=conversation_ctx,
                    response_data={"status_result": device_result}
                )
                
            elif intent.get("requires_memory", False):
                # Memory retrieval flow
                memories = await self._retrieve_memory(
                    intent["memory_query"], 
                    user_id
                )
                
                # Update context with memories
                conversation_ctx.current_intent.update({
                    "memories": memories
                })
                response = await self.character_system.generate_response(
                    context=conversation_ctx,
                    response_data={"memories": memories}
                )
                
            else:
                # Pure conversational flow
                response = await self.character_system.generate_response(
                    context=conversation_ctx,
                    response_data=None
                )

            # Add assistant response to history using the context manager method
            conversation_ctx.add_assistant_response(response)

            # Save to database
            self.db_service.save_message(
                conversation_id=conv_id,
                user_input=user_input,
                assistant_response=response,
                tone_used=conversation_ctx.conversation_tone,
                intent_detected=intent
            )

            return response, conv_id
            
        except Exception as e:
            self.logger.error(f"Task planner error: {e}")
            
            # Fallback response
            if conversation_ctx.current_intent is None:
                conversation_ctx.current_intent = {}
            conversation_ctx.current_intent.update({
                "error": str(e)
            })
            response = await self.character_system.generate_response(
                context=conversation_ctx,
                response_data={"error": str(e)}
            )
            # Add fallback response to history using the context manager method
            conversation_ctx.add_assistant_response(response)

            return response, conv_id
    
    async def _retrieve_memory(self, query: str, user_id: str) -> list:
        """Retrieve user memories"""
        memories = self.db_service.search_user_memories(user_id, query, limit=5)
        return [memory.to_dict() for memory in memories]
