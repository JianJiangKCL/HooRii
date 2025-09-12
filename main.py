#!/usr/bin/env python3
"""
Home AI System Main Application
Orchestrates intent analysis, device control, and character responses with full context awareness
"""
import asyncio
import json
import uuid
import logging
from typing import Dict, Optional, Any
from datetime import datetime
import os

# Disable OpenTelemetry exporters to avoid auth errors
os.environ['OTEL_TRACES_EXPORTER'] = 'none'
os.environ['OTEL_METRICS_EXPORTER'] = 'none'
os.environ['OTEL_LOGS_EXPORTER'] = 'none'
os.environ['OTEL_SDK_DISABLED'] = 'false'

import anthropic

# Try to import Langfuse components
try:
    from langfuse import Langfuse, observe, get_client
    LANGFUSE_AVAILABLE = True
    print("✅ Langfuse available")
except ImportError:
    print("⚠️ Warning: Langfuse not available, observability will be disabled")
    LANGFUSE_AVAILABLE = False
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    Langfuse = None
    get_client = None

from config import Config, load_config
from database_service import DatabaseService
from context_manager import ContextManager, SystemContext
from intent_analyzer import IntentAnalyzer
from device_controller import DeviceController
from character_system import CharacterSystem
from langfuse_session_manager import LangfuseSessionManager


class HomeAISystem:
    """Main orchestrator for the Home AI system with context-aware processing"""
    
    def __init__(self, config: Config = None):
        # Load configuration
        self.config = config or load_config()
        
        # Setup logging
        logging.basicConfig(level=getattr(logging, self.config.system.log_level))
        self.logger = logging.getLogger(__name__)
        
        # Initialize context manager
        self.context_manager = ContextManager()
        
        # Initialize database service
        self.db_service = DatabaseService(self.config)
        self.db_service.initialize_default_data()
        
        # Initialize components
        self.intent_analyzer = IntentAnalyzer(self.config)
        self.device_controller = DeviceController(self.config)
        self.character_system = CharacterSystem(self.config)
        
        # Initialize session manager
        self.session_manager = LangfuseSessionManager(self.config)
        
        # Initialize Langfuse for observability
        self.langfuse_enabled = self.config.langfuse.enabled and LANGFUSE_AVAILABLE
        self.current_trace = None  # Track current session trace
        
        if self.langfuse_enabled:
            try:
                os.environ['LANGFUSE_SECRET_KEY'] = self.config.langfuse.secret_key
                os.environ['LANGFUSE_PUBLIC_KEY'] = self.config.langfuse.public_key
                os.environ['LANGFUSE_HOST'] = self.config.langfuse.host
                
                self.langfuse = Langfuse(
                    secret_key=self.config.langfuse.secret_key,
                    public_key=self.config.langfuse.public_key,
                    host=self.config.langfuse.host
                )
            except Exception as e:
                self.logger.warning(f"Failed to initialize Langfuse: {e}")
                self.langfuse_enabled = False
                self.langfuse = None
        else:
            self.langfuse = None
        
        print("🏠 Home AI System initialized with context awareness")
        self.config.print_config()
    
    def _setup_langfuse_session(self, session_id: str, user_id: str = None):
        """Setup Langfuse session and user tracking"""
        if not self.langfuse_enabled or not self.langfuse:
            return
            
        try:
            # Create a new trace for this session
            trace_metadata = {
                "session_id": session_id,
                "system": "home_ai_assistant",
                "tags": ["conversation", "session"]
            }
            
            if user_id:
                trace_metadata["user_id"] = user_id
                
            # Create a session span for tracking
            self.current_trace = self.langfuse.start_as_current_span(
                name="conversation_session",
                metadata={
                    **trace_metadata,
                    "user_id": user_id
                }
            )
            
            # Update trace with session ID using the new API
            self.langfuse.update_current_trace(
                session_id=session_id,
                user_id=user_id,
                metadata=trace_metadata
            )
            
            self.logger.debug(f"Langfuse session setup: session_id={session_id}, user_id={user_id}")
                
        except Exception as e:
            self.logger.warning(f"Failed to setup Langfuse session: {e}")
    
    @observe(as_type="generation", name="process_user_input")
    async def process_user_input(
        self,
        user_input: str,
        user_id: str = None,
        session_id: str = None
    ) -> str:
        """Main entry point for processing user input with full context flow"""
        
        # Create or get session context
        if not session_id:
            session_id = str(uuid.uuid4())
        
        context = self.context_manager.get_context()
        if not context.session_id:
            context = self.context_manager.create_session(session_id)
        
        # Setup Langfuse session and user tracking
        self._setup_langfuse_session(session_id, user_id)
        
        # Start session if this is a new session
        if context.message_count == 0:
            self.session_manager.start_session(
                session_id=session_id,
                user_id=user_id,
                metadata={
                    "familiarity_score": context.familiarity_score,
                    "conversation_tone": context.conversation_tone
                }
            )
        
        # Add session metadata for Langfuse
        if self.langfuse_enabled and self.langfuse:
            try:
                # Update current trace with interaction metadata
                self.langfuse.update_current_trace(
                    metadata={
                        "message_count": context.message_count + 1,
                        "conversation_tone": context.conversation_tone,
                        "familiarity_score": context.familiarity_score
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to update trace metadata: {e}")
        
        # Update context with user input
        context.user_input = user_input
        context.timestamp = datetime.now()
        
        # Get user familiarity from database
        if user_id:
            context.familiarity_score = self.db_service.get_user_familiarity(user_id)
            
            # Update Langfuse with user metadata
            if self.langfuse_enabled and self.langfuse:
                try:
                    # Get user data safely within proper session context
                    user_data = self.db_service.get_user_metadata(user_id)
                    self.langfuse.update_current_trace(
                        metadata={
                            "user_interaction_count": user_data.get("interaction_count", 0),
                            "user_familiarity": context.familiarity_score,
                            "user_created_at": user_data.get("created_at")
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to update Langfuse with user metadata: {e}")
        else:
            context.familiarity_score = 50  # Default familiarity
        
        # Update conversation tone based on familiarity
        if context.familiarity_score < 30:
            context.conversation_tone = "formal"
        elif context.familiarity_score < 70:
            context.conversation_tone = "neutral"
        else:
            context.conversation_tone = "friendly"
        
        try:
            # Step 1: Analyze intent with context
            self.logger.debug(f"Analyzing intent for: {user_input}")
            intent = await self.intent_analyzer.analyze_intent(
                user_input=user_input,
                context=context
            )
            
            # Step 2: Process based on intent type
            response_data = None
            
            if intent.get("involves_hardware"):
                # Check familiarity requirement
                device_id = intent.get("device")
                if device_id:
                    familiarity_check = await self.device_controller.check_familiarity_requirement(
                        device_id=device_id,
                        action=intent.get("action"),
                        context=context
                    )
                    
                    if not familiarity_check.get("allowed"):
                        # Generate rejection response
                        response_data = {
                            "insufficient_familiarity": True,
                            "required_score": familiarity_check.get("required_score"),
                            "message": familiarity_check.get("message")
                        }
                    else:
                        # Process device intent
                        self.logger.info("Processing device control intent")
                        response_data = await self.device_controller.process_device_intent(
                            intent=intent,
                            context=context
                        )
            
            elif intent.get("requires_status_query"):
                # Process status query
                self.logger.info("Processing device status query")
                response_data = await self.device_controller.process_device_intent(
                    intent=intent,
                    context=context
                )
            
            elif intent.get("requires_memory"):
                # Retrieve memories if needed
                self.logger.info("Retrieving memories")
                memories = self.db_service.search_user_memories(
                    user_id=user_id or session_id,
                    query=intent.get("memory_query", user_input),
                    limit=5
                )
                context.relevant_memories = [
                    {
                        "content": m.content,
                        "timestamp": m.created_at.isoformat() if m.created_at else None,
                        "type": m.memory_type
                    }
                    for m in memories
                ]
                response_data = {"memories_retrieved": len(memories)}
            
            # Step 3: Generate character response with full context
            self.logger.debug("Generating character response")
            final_response = await self.character_system.generate_response(
                context=context,
                response_data=response_data
            )
            
            # Steps 4-6: Database and session operations (async, non-blocking for user response)
            # Start these tasks in background after user gets response
            asyncio.create_task(self._handle_post_response_operations(
                user_id, session_id, user_input, final_response, intent, context, response_data
            ))
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"Error processing user input: {e}")
            
            # Generate error response through character system
            error_response = await self.character_system.generate_response(
                context=context,
                response_data={"error": str(e)}
            )
            
            return error_response
    
    async def _handle_post_response_operations(
        self, user_id: str, session_id: str, user_input: str, 
        final_response: str, intent: dict, context, response_data: dict
    ):
        """Handle database and session operations in background after user gets response"""
        try:
            if user_id:
                # Get or create conversation
                try:
                    db_conversation = self.db_service.get_or_create_conversation(
                        user_id=user_id,
                        conversation_id=session_id
                    )
                except Exception as db_error:
                    self.logger.warning(f"Database conversation error: {db_error}")
                    # Try to get existing conversation by ID
                    session = self.db_service.get_session()
                    try:
                        from models import Conversation
                        db_conversation = session.query(Conversation).filter_by(id=session_id).first()
                    finally:
                        session.close()
                    if not db_conversation:
                        # Create with unique ID
                        import uuid
                        session_id = f"{session_id}_{str(uuid.uuid4())[:8]}"
                        db_conversation = self.db_service.get_or_create_conversation(
                            user_id=user_id,
                            conversation_id=session_id
                        )
                
                # Save message - use session_id directly to avoid SQLAlchemy session issues
                self.db_service.save_message(
                    conversation_id=session_id,
                    user_input=user_input,
                    assistant_response=final_response,
                    intent_detected=intent,
                    tone_used=context.conversation_tone
                )
                
                # Update user interaction count for familiarity
                try:
                    self.db_service.increment_user_interaction(user_id)
                except Exception as e:
                    self.logger.warning(f"Failed to increment user interaction count: {e}")
            
            # Track interaction in session
            self.session_manager.track_interaction(
                session_id=session_id,
                user_input=user_input,
                assistant_response=final_response,
                metadata={
                    "intent_type": "hardware" if intent.get("involves_hardware") else "conversation",
                    "device_involved": intent.get("device"),
                    "success": response_data.get("success", True) if response_data else True
                }
            )
            
            # Save context for persistence (async, non-blocking)
            await self.context_manager.save_context_async(f"contexts/{session_id}.json")
                
        except Exception as save_error:
            # Log database/session errors but don't let them affect the user response
            self.logger.warning(f"Non-critical backend operations failed: {save_error}")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Save any active contexts
            if self.context_manager.context.session_id:
                self.context_manager.save_context(
                    f"contexts/{self.context_manager.context.session_id}.json"
                )
            
            # Cleanup database connections
            self.db_service.cleanup_expired_conversations()
            
            # End Langfuse session and flush
            if self.session_manager and self.context_manager.context.session_id:
                self.session_manager.end_session(
                    session_id=self.context_manager.context.session_id,
                    final_metadata={
                        "session_ended": True,
                        "session_duration_minutes": (datetime.now() - self.context_manager.context.timestamp).total_seconds() / 60,
                        "final_message_count": self.context_manager.context.message_count,
                        "final_familiarity_score": self.context_manager.context.familiarity_score
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


async def main():
    """Main entry point for testing"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Home AI Assistant')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug logging (shows detailed info, debug, and error messages)')
    args = parser.parse_args()
    
    # Configure logging level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        print("🐛 Debug mode enabled - showing detailed logs")
    else:
        logging.getLogger().setLevel(logging.WARNING)  # Only show warnings and errors
    
    system = HomeAISystem()
    
    print("\n🤖 Home AI Assistant Ready!")
    print("Type 'exit' to quit, 'reset' to start a new session")
    if args.debug:
        print("🔍 Debug mode: ON")
    print()
    
    session_id = str(uuid.uuid4())
    user_id = "test_user"
    
    try:
        while True:
            user_input = input("\n你: ").strip()
            
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'reset':
                session_id = str(uuid.uuid4())
                system.context_manager.create_session(session_id)
                print("✨ Started new session")
                continue
            elif not user_input:
                continue
            
            # Process input
            response = await system.process_user_input(
                user_input=user_input,
                user_id=user_id,
                session_id=session_id
            )
            
            print(f"\n凌波丽: {response}")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    finally:
        await system.cleanup()


if __name__ == "__main__":
    asyncio.run(main())