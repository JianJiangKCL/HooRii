#!/usr/bin/env python3
"""
Context Manager Component
Manages conversation context and state across all components
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging


@dataclass
class SystemContext:
    """Complete system context shared across components"""
    
    # User conversation context
    user_input: str = ""
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    message_count: int = 0
    familiarity_score: int = 0
    conversation_tone: str = "neutral"  # neutral, friendly, intimate
    
    # Device context
    device_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_device_action: Optional[Dict[str, Any]] = None
    previous_device_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Intent context
    current_intent: Optional[Dict[str, Any]] = None
    previous_intents: List[Dict[str, Any]] = field(default_factory=list)
    reference_resolution: Dict[str, Any] = field(default_factory=dict)  # 解析指代词
    
    # Memory context
    relevant_memories: List[Dict[str, Any]] = field(default_factory=list)
    memory_query_result: Optional[str] = None
    
    # Response context
    last_response: Optional[str] = None
    response_history: List[str] = field(default_factory=list)
    
    # Metadata
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_user_message(self, user_msg: str, max_history: int = 20):
        """Add user message to history (called at start of processing)"""
        self.conversation_history.append({
            "role": "user",
            "content": user_msg,
            "timestamp": datetime.now().isoformat()
        })
        self.message_count += 1
        self.user_input = user_msg
        
        # Keep history size manageable (only if not unlimited)
        if max_history > 0 and len(self.conversation_history) > max_history * 2:
            self.conversation_history = self.conversation_history[-(max_history * 2):]
    
    def add_assistant_response(self, assistant_msg: str, max_history: int = 20):
        """Add assistant response to history (called after generation)"""
        self.conversation_history.append({
            "role": "assistant", 
            "content": assistant_msg,
            "timestamp": datetime.now().isoformat()
        })
        self.message_count += 1
        self.last_response = assistant_msg
        self.response_history.append(assistant_msg)
        
        # Keep history size manageable (only if not unlimited)
        if max_history > 0 and len(self.conversation_history) > max_history * 2:
            self.conversation_history = self.conversation_history[-(max_history * 2):]
    
    def add_conversation_turn(self, user_msg: str, assistant_msg: str):
        """Add a complete conversation turn to history (legacy method for compatibility)"""
        self.add_user_message(user_msg)
        self.add_assistant_response(assistant_msg)
            
    def update_device_state(self, device_id: str, state: Dict[str, Any]):
        """Update device state and maintain history"""
        if device_id in self.device_states:
            self.previous_device_states[device_id] = self.device_states[device_id].copy()
        self.device_states[device_id] = state
        self.last_device_action = {
            "device": device_id,
            "state": state,
            "timestamp": datetime.now().isoformat()
        }
        
    def add_intent(self, intent: Dict[str, Any]):
        """Add intent analysis result"""
        self.current_intent = intent
        self.previous_intents.append(intent)
        
        # Keep intent history size manageable
        if len(self.previous_intents) > 10:
            self.previous_intents = self.previous_intents[-10:]
            
    def resolve_reference(self, reference: str) -> Optional[str]:
        """Resolve references like '它', '那个' based on context"""
        if reference in ["它", "那个", "这个"]:
            # Check last device action
            if self.last_device_action:
                return self.last_device_action.get("device")
            # Check previous intents for device mentions
            for intent in reversed(self.previous_intents[-3:]):
                if intent.get("device"):
                    return intent["device"]
        return None
        
    def get_conversation_context_for_llm(self, max_turns: Optional[int] = None) -> str:
        """Get formatted conversation history for LLM (legacy string format)"""
        if max_turns is None:
            # Use all available history
            recent_history = self.conversation_history
        elif max_turns == -1:
            # Unlimited history
            recent_history = self.conversation_history
        else:
            # Limited history
            recent_history = self.conversation_history[-(max_turns * 2):]
        
        formatted = []
        for msg in recent_history:
            role = "用户" if msg["role"] == "user" else "助手"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)
    
    def get_conversation_messages_for_llm(self, max_turns: Optional[int] = None) -> List[Dict[str, str]]:
        """Get conversation history in standard message format for LLM"""
        if max_turns is None:
            # Use all available history
            recent_history = self.conversation_history
        elif max_turns == -1:
            # Unlimited history
            recent_history = self.conversation_history
        else:
            # Limited history
            recent_history = self.conversation_history[-(max_turns * 2):]
        
        # Only return user and assistant messages (simplified)
        return [{"role": msg["role"], "content": msg["content"]} for msg in recent_history]
        
    def get_device_context_for_llm(self) -> str:
        """Get formatted device state for LLM"""
        if not self.device_states:
            return "暂无设备状态信息"
            
        device_info = []
        for device_id, state in self.device_states.items():
            status = "开启" if state.get("status") == "on" else "关闭"
            info = f"- {device_id}: {status}"
            
            # Add extra properties
            if "brightness" in state:
                info += f", 亮度: {state['brightness']}%"
            if "temperature" in state:
                info += f", 温度: {state['temperature']}°C"
            if "volume" in state:
                info += f", 音量: {state['volume']}%"
                
            device_info.append(info)
            
        return "当前设备状态:\n" + "\n".join(device_info)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization"""
        return {
            "user_input": self.user_input,
            "conversation_history": self.conversation_history,
            "message_count": self.message_count,
            "familiarity_score": self.familiarity_score,
            "conversation_tone": self.conversation_tone,
            "device_states": self.device_states,
            "last_device_action": self.last_device_action,
            "current_intent": self.current_intent,
            "previous_intents": self.previous_intents,
            "reference_resolution": self.reference_resolution,
            "relevant_memories": self.relevant_memories,
            "last_response": self.last_response,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat()
        }


class ContextManager:
    """Manages system context across components"""
    
    def __init__(self, max_turns: int = 20):
        self.logger = logging.getLogger(__name__)
        self.context = SystemContext()
        self.max_turns = max_turns
        
    def create_session(self, session_id: str) -> SystemContext:
        """Create a new session context"""
        self.context = SystemContext(session_id=session_id)
        self.logger.debug(f"Created new session: {session_id}")
        return self.context
        
    def get_context(self) -> SystemContext:
        """Get current context"""
        return self.context
        
    def update_context(self, **kwargs):
        """Update context fields"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                # Normalize timestamp back to datetime when coming from serialized dict
                if key == "timestamp" and isinstance(value, str):
                    try:
                        from datetime import datetime
                        value = datetime.fromisoformat(value)
                    except Exception:
                        pass
                setattr(self.context, key, value)
                
    def save_context(self, filepath: str):
        """Save context to file (synchronous)"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.context.to_dict(), f, ensure_ascii=False, indent=2)
            self.logger.info(f"Context saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save context: {e}")
    
    async def save_context_async(self, filepath: str):
        """Save context to file asynchronously"""
        import asyncio
        try:
            # Run file I/O in a thread pool to avoid blocking
            await asyncio.to_thread(self._save_context_sync, filepath)
        except Exception as e:
            self.logger.error(f"Failed to save context asynchronously: {e}")
    
    def _save_context_sync(self, filepath: str):
        """Internal synchronous context save"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.context.to_dict(), f, ensure_ascii=False, indent=2)
        self.logger.info(f"Context saved to {filepath}")
            
    def load_context(self, filepath: str) -> SystemContext:
        """Load context from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.context = SystemContext()
            for key, value in data.items():
                if hasattr(self.context, key):
                    if key == "timestamp":
                        value = datetime.fromisoformat(value)
                    setattr(self.context, key, value)
                    
            self.logger.info(f"Context loaded from {filepath}")
            return self.context
        except Exception as e:
            self.logger.error(f"Failed to load context: {e}")
            return SystemContext()