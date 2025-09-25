#!/usr/bin/env python3
"""
Langfuse Session Manager
Handles proper session tracking and management for Langfuse observability
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Try to import Langfuse components
try:
    from langfuse import Langfuse
    from langfuse.decorators import langfuse_context, observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    langfuse_context = None
    Langfuse = None


class LangfuseSessionManager:
    """Manages Langfuse sessions for conversation tracking"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.langfuse_enabled = config.langfuse.enabled and LANGFUSE_AVAILABLE
        self.langfuse = None
        
        if self.langfuse_enabled:
            try:
                self.langfuse = Langfuse(
                    secret_key=config.langfuse.secret_key,
                    public_key=config.langfuse.public_key,
                    host=config.langfuse.host
                )
            except Exception as e:
                self.logger.warning(f"Failed to initialize Langfuse: {e}")
                self.langfuse_enabled = False
    
    def start_session(self, session_id: str, user_id: str = None, metadata: Dict[str, Any] = None):
        """Start a new session with proper Langfuse tracking"""
        if not self.langfuse_enabled or not self.langfuse:
            return
            
        try:
            # Create a trace for this session
            trace_data = {
                "id": f"session_{session_id}",
                "session_id": session_id,
                "name": "conversation_session",
                "metadata": {
                    "session_start": datetime.now().isoformat(),
                    "system": "home_ai_assistant",
                    **(metadata or {})
                },
                "tags": ["conversation", "session"]
            }
            
            if user_id:
                trace_data["user_id"] = user_id
            
            # Create the session trace
            trace = self.langfuse.trace(**trace_data)
            
            self.logger.info(f"Started Langfuse session: {session_id} for user: {user_id}")
            return trace
            
        except Exception as e:
            self.logger.warning(f"Failed to start Langfuse session: {e}")
            return None
    
    def update_session_context(self, session_id: str, metadata: Dict[str, Any]):
        """Update session context with new metadata"""
        if not self.langfuse_enabled or not langfuse_context:
            return
            
        try:
            langfuse_context.update_current_trace(
                session_id=session_id,
                metadata=metadata
            )
        except Exception as e:
            self.logger.warning(f"Failed to update session context: {e}")
    
    def add_session_event(self, session_id: str, event_name: str, event_data: Dict[str, Any]):
        """Add an event to the current session"""
        if not self.langfuse_enabled or not self.langfuse:
            return
            
        try:
            # Create an event within the session
            self.langfuse.event(
                name=event_name,
                session_id=session_id,
                metadata=event_data
            )
        except Exception as e:
            self.logger.warning(f"Failed to add session event: {e}")
    
    def end_session(self, session_id: str, final_metadata: Dict[str, Any] = None):
        """End a session with final metadata"""
        if not self.langfuse_enabled:
            return
            
        try:
            if final_metadata and langfuse_context:
                langfuse_context.update_current_trace(
                    metadata={
                        "session_end": datetime.now().isoformat(),
                        **(final_metadata or {})
                    }
                )
            
            if self.langfuse:
                self.langfuse.flush()
                
            self.logger.info(f"Ended Langfuse session: {session_id}")
            
        except Exception as e:
            self.logger.warning(f"Failed to end Langfuse session: {e}")
    
    @observe(as_type="span", name="session_interaction")
    def track_interaction(self, session_id: str, user_input: str, assistant_response: str, metadata: Dict[str, Any] = None):
        """Track a single interaction within a session"""
        if not self.langfuse_enabled:
            return
            
        try:
            # Update current trace with session context
            if langfuse_context:
                langfuse_context.update_current_trace(
                    session_id=session_id,
                    input=user_input,
                    output=assistant_response,
                    metadata=metadata or {}
                )
                
        except Exception as e:
            self.logger.warning(f"Failed to track interaction: {e}")