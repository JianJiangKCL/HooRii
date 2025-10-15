#!/usr/bin/env python3
"""
Optimized Workflow - Single API Call
Combines intent analysis and character response generation into ONE LLM call
Reduces latency by ~50% compared to traditional workflow
"""
import asyncio
import logging
import uuid
from typing import Optional
from datetime import datetime

try:
    from langfuse import observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from ..core.unified_responder import UnifiedResponder
from ..core.device_controller import DeviceController
from ..core.context_manager import ContextManager, SystemContext
from ..services.database_service import DatabaseService
from ..utils.config import Config


class OptimizedHomeAISystem:
    """
    Optimized Home AI System with single LLM call
    
    Performance improvements:
    - 1 LLM call instead of 2 (intent + response merged)
    - ~50% faster response time
    - Reduced API costs
    - Familiarity score explicitly used in unified prompt
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.unified_responder = UnifiedResponder(config)
        self.device_controller = DeviceController(config)
        self.context_manager = ContextManager(max_turns=config.system.max_conversation_turns)
        self.db_service = DatabaseService(config)
        
        # Langfuse setup
        self.langfuse_enabled = False
        self.langfuse = None
        
        if LANGFUSE_AVAILABLE and config.langfuse.enabled:
            try:
                from langfuse import Langfuse
                self.langfuse = Langfuse(
                    public_key=config.langfuse.public_key,
                    secret_key=config.langfuse.secret_key,
                    host=config.langfuse.host
                )
                self.langfuse_enabled = True
                self.logger.info("✅ Langfuse observability enabled (optimized mode)")
            except Exception as e:
                self.logger.warning(f"Langfuse initialization failed: {e}")
                self.langfuse_enabled = False
        
        print("🚀 Optimized Home AI System initialized (Single LLM Call Mode)")
        self.config.print_config()
    
    @observe(as_type="generation", name="optimized_process_user_input")
    async def process_user_input(
        self,
        user_input: str,
        user_id: str = None,
        session_id: str = None
    ) -> str:
        """
        Main entry point for processing user input with optimized single-call workflow
        
        Workflow:
        1. Load context with familiarity score
        2. Single LLM call for intent + response
        3. Execute device control if needed (parallel with response return)
        4. Background operations (DB save, etc.)
        
        Returns: Character response (string)
        """
        
        start_time = datetime.now()
        
        # Create or get session context
        if not session_id:
            session_id = str(uuid.uuid4())
        
        context = self.context_manager.get_context()
        if not context.session_id:
            context = self.context_manager.create_session(session_id)
        
        # Ensure user exists in database
        if user_id:
            self.db_service.get_or_create_user(user_id)
        
        # Update context with user input
        context.user_input = user_input
        context.timestamp = datetime.now()
        
        # CRITICAL: Load user familiarity from database
        if user_id:
            context.familiarity_score = self.db_service.get_user_familiarity(user_id)
            self.logger.info(f"📊 User familiarity loaded: {context.familiarity_score}/100")
            
            # Update Langfuse metadata
            if self.langfuse_enabled and self.langfuse:
                try:
                    user_data = self.db_service.get_user_metadata(user_id)
                    self.langfuse.update_current_trace(
                        metadata={
                            "user_interaction_count": user_data.get("interaction_count", 0),
                            "user_familiarity": context.familiarity_score,
                            "workflow_type": "optimized_single_call"
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to update Langfuse metadata: {e}")
        else:
            context.familiarity_score = self.config.system.default_familiarity_score
            self.logger.info(f"📊 Using default familiarity: {context.familiarity_score}/100")
        
        # Update conversation tone based on familiarity
        if context.familiarity_score < 30:
            context.conversation_tone = "formal"
        elif context.familiarity_score < 70:
            context.conversation_tone = "neutral"
        else:
            context.conversation_tone = "friendly"
        
        try:
            # OPTIMIZED: Single LLM call for both intent and response
            self.logger.info("🚀 Starting unified processing (1 API call)")
            
            unified_result = await self.unified_responder.process_and_respond(
                user_input=user_input,
                context=context
            )
            
            if not unified_result.get("success"):
                # Return error response directly
                error_response = unified_result.get("response", "......出现了问题。")
                return error_response
            
            intent = unified_result["intent"]
            final_response = unified_result["response"]
            
            # Check if device control is needed
            device_result = None
            if intent.get("involves_hardware") and intent.get("familiarity_check") == "passed":
                self.logger.info(f"🔧 Device control needed: {intent.get('device')}")
                
                # Execute device control (can be async in background)
                try:
                    device_result = await self.device_controller.process_device_intent(
                        intent=intent,
                        context=context
                    )
                    
                    # Log device interaction
                    if device_result.get("success"):
                        self.logger.info(f"✅ Device control succeeded: {device_result.get('message')}")
                    else:
                        self.logger.warning(f"⚠️ Device control failed: {device_result.get('error')}")
                        
                except Exception as e:
                    self.logger.error(f"Device control error: {e}")
                    device_result = {"success": False, "error": str(e)}
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.info(f"⏱️ Processing time: {processing_time:.0f}ms")
            
            # Background operations (non-blocking)
            asyncio.create_task(self._handle_post_response_operations(
                user_id=user_id,
                session_id=session_id,
                user_input=user_input,
                final_response=final_response,
                intent=intent,
                context=context,
                device_result=device_result,
                processing_time=processing_time
            ))
            
            return final_response
        
        except Exception as e:
            self.logger.error(f"Error in optimized workflow: {e}")
            
            # Generate error response in character
            if context.familiarity_score < 30:
                error_response = "......出现了问题。"
            elif context.familiarity_score < 60:
                error_response = "......系统出错了。稍等。"
            else:
                error_response = f"......出了点问题。让我看看......({str(e)[:20]})"
            
            return error_response
    
    async def _handle_post_response_operations(
        self,
        user_id: str,
        session_id: str,
        user_input: str,
        final_response: str,
        intent: dict,
        context: SystemContext,
        device_result: Optional[dict],
        processing_time: float
    ):
        """Handle post-response operations in background"""
        
        try:
            # Save message to database
            if user_id and session_id:
                # Get or create conversation
                conversation = self.db_service.get_or_create_conversation(
                    user_id=user_id,
                    conversation_id=session_id
                )
                
                # Save message
                self.db_service.save_message(
                    conversation_id=conversation.id,
                    user_input=user_input,
                    assistant_response=final_response,
                    tone_used=context.conversation_tone,
                    intent_detected=intent,
                    tools_used=["unified_responder", "device_controller"] if device_result else ["unified_responder"],
                    processing_time_ms=processing_time
                )
                
                # Increment user interaction count
                self.db_service.increment_user_interaction(user_id)
                
                # Log device interaction if any
                if device_result and intent.get("involves_hardware"):
                    self.db_service.log_device_interaction(
                        user_id=user_id,
                        device_id=intent.get("device", "unknown"),
                        action=intent.get("action", "unknown"),
                        parameters=intent.get("parameters", {}),
                        result=device_result,
                        success=device_result.get("success", False),
                        conversation_id=session_id
                    )
            
            # Update context history
            context.add_user_message(user_input)
            context.add_assistant_response(final_response)
            
            self.logger.debug("✅ Background operations completed")
            
        except Exception as e:
            self.logger.error(f"Post-response operations error: {e}")
    
    async def get_session_info(self, session_id: str) -> dict:
        """Get session information"""
        # Get from database
        conversations = self.db_service.get_recent_conversations_for_user(session_id, limit=1)
        if conversations:
            conv = conversations[0]
            return {
                "session_id": conv.id,
                "user_id": conv.user_id,
                "is_active": conv.is_active,
                "last_activity": conv.last_activity.isoformat() if conv.last_activity else None
            }
        return {}
    
    async def end_session(self, session_id: str):
        """End a session"""
        # End conversation in database
        self.db_service.end_conversation(session_id)
        
        self.logger.info(f"Session ended: {session_id}")


# Factory function for creating optimized system
def create_optimized_system(config: Config) -> OptimizedHomeAISystem:
    """Create an optimized home AI system instance"""
    return OptimizedHomeAISystem(config)

