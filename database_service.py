"""
Database service layer for the Smart Home AI Assistant
Replaces the mock databases with real database operations
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, String

from models import (
    User, Conversation, Message, UserMemory, Device, 
    DeviceInteraction, SystemSettings, DatabaseManager
)
from config import Config

class DatabaseService:
    """Service layer for database operations"""
    
    def __init__(self, config: Config):
        self.config = config
        self.db_manager = DatabaseManager(config.database.url)
        self.db_manager.create_tables()
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.db_manager.get_session()
    
    # User Management
    def get_or_create_user(self, user_id: str, username: str = None, **kwargs) -> User:
        """Get existing user or create new one"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                user = User(
                    id=user_id,
                    username=username or user_id,
                    familiarity_score=self.config.system.default_familiarity_score,
                    **kwargs
                )
                session.add(user)
                session.commit()
                session.refresh(user)
                print(f"✅ Created new user: {user_id}")
            else:
                # Update last_seen
                user.last_seen = datetime.utcnow()
                session.commit()
            
            return user
        finally:
            session.close()
    
    def update_user_familiarity(self, user_id: str, score: int) -> bool:
        """Update user's familiarity score"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.familiarity_score = max(0, min(100, score))
                user.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def get_user_familiarity(self, user_id: str) -> int:
        """Get user's familiarity score"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                return user.familiarity_score
            return self.config.system.default_familiarity_score
        finally:
            session.close()
    
    # Conversation Management
    def get_or_create_conversation(
        self, 
        user_id: str, 
        conversation_id: str = None
    ) -> Conversation:
        """Get existing conversation or create new one"""
        session = self.get_session()
        try:
            # Ensure user exists
            user = self.get_or_create_user(user_id)
            
            if conversation_id:
                conversation = session.query(Conversation).filter_by(
                    id=conversation_id,
                    user_id=user_id
                ).first()
                
                if conversation and not conversation.is_expired:
                    conversation.update_activity()
                    session.commit()
                    return conversation
            
            # Create new conversation
            conversation = Conversation(
                id=conversation_id or str(uuid.uuid4()),
                user_id=user_id,
                title=f"对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            return conversation
        finally:
            session.close()
    
    def end_conversation(self, conversation_id: str) -> bool:
        """End a conversation"""
        session = self.get_session()
        try:
            conversation = session.query(Conversation).filter_by(id=conversation_id).first()
            if conversation:
                conversation.is_active = False
                conversation.end_time = datetime.utcnow()
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def cleanup_expired_conversations(self) -> int:
        """Clean up expired conversations"""
        session = self.get_session()
        try:
            timeout_time = datetime.utcnow() - timedelta(
                minutes=self.config.system.conversation_timeout_minutes
            )
            
            expired_conversations = session.query(Conversation).filter(
                and_(
                    Conversation.is_active == True,
                    Conversation.last_activity < timeout_time
                )
            ).all()
            
            count = 0
            for conv in expired_conversations:
                conv.is_active = False
                conv.end_time = datetime.utcnow()
                count += 1
            
            session.commit()
            return count
        finally:
            session.close()
    
    def get_conversation_history(
        self, 
        conversation_id: str, 
        limit: int = 10
    ) -> List[Message]:
        """Get conversation history"""
        session = self.get_session()
        try:
            messages = session.query(Message).filter_by(
                conversation_id=conversation_id
            ).order_by(desc(Message.timestamp)).limit(limit).all()
            
            return list(reversed(messages))  # Return in chronological order
        finally:
            session.close()
    
    # Message Management
    def save_message(
        self,
        conversation_id: str,
        user_input: str = None,
        assistant_response: str = None,
        tone_used: str = None,
        intent_detected: dict = None,
        tools_used: List[str] = None,
        langfuse_trace_id: str = None,
        processing_time_ms: float = None
    ) -> Message:
        """Save a message to the database"""
        session = self.get_session()
        try:
            message = Message(
                conversation_id=conversation_id,
                user_input=user_input,
                assistant_response=assistant_response,
                tone_used=tone_used,
                intent_detected=intent_detected or {},
                tools_used=tools_used or [],
                langfuse_trace_id=langfuse_trace_id,
                processing_time_ms=processing_time_ms
            )
            session.add(message)
            session.commit()
            session.refresh(message)
            return message
        finally:
            session.close()
    
    # User Memory Management
    def save_user_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "general",
        keywords: List[str] = None,
        source_conversation_id: str = None,
        importance_score: float = 1.0
    ) -> UserMemory:
        """Save a user memory"""
        session = self.get_session()
        try:
            memory = UserMemory(
                user_id=user_id,
                content=content,
                memory_type=memory_type,
                keywords=keywords or [],
                source_conversation_id=source_conversation_id,
                importance_score=importance_score
            )
            session.add(memory)
            session.commit()
            session.refresh(memory)
            return memory
        finally:
            session.close()
    
    def search_user_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        memory_type: str = None
    ) -> List[UserMemory]:
        """Search user memories by keywords"""
        session = self.get_session()
        try:
            # Simple keyword search for now
            query_words = query.lower().split()
            
            base_query = session.query(UserMemory).filter_by(user_id=user_id)
            
            if memory_type:
                base_query = base_query.filter_by(memory_type=memory_type)
            
            # Search in content and keywords (JSON array search for SQLite compatibility)
            search_conditions = []
            for word in query_words:
                search_conditions.append(
                    or_(
                        func.lower(UserMemory.content).contains(word),
                        func.lower(UserMemory.keywords.cast(String)).contains(f'"{word.lower()}"')
                    )
                )
            
            if search_conditions:
                base_query = base_query.filter(or_(*search_conditions))
            
            memories = base_query.order_by(
                desc(UserMemory.importance_score),
                desc(UserMemory.last_accessed)
            ).limit(limit).all()
            
            # Update access info and convert to dicts to avoid session issues
            memory_data = []
            for memory in memories:
                memory.last_accessed = datetime.utcnow()
                memory.access_count += 1
                # Convert to dict immediately while session is active
                memory_data.append({
                    'id': memory.id,
                    'user_id': memory.user_id,
                    'content': memory.content,
                    'memory_type': memory.memory_type,
                    'keywords': memory.keywords,
                    'created_at': memory.created_at.isoformat() if memory.created_at else None,
                    'last_accessed': memory.last_accessed.isoformat(),
                    'access_count': memory.access_count,
                    'importance_score': memory.importance_score
                })
            session.commit()
            
            # Convert back to UserMemory-like objects for compatibility
            result_memories = []
            for data in memory_data:
                mem = UserMemory()
                for key, value in data.items():
                    if key in ['created_at', 'last_accessed'] and value:
                        setattr(mem, key, datetime.fromisoformat(value.replace('Z', '+00:00')))
                    else:
                        setattr(mem, key, value)
                result_memories.append(mem)
            
            return result_memories
        finally:
            session.close()
    
    def get_user_preferences(self, user_id: str) -> Dict:
        """Get user preferences and recent memories"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return {}
            
            # Get general preferences and habits
            preferences = session.query(UserMemory).filter(
                and_(
                    UserMemory.user_id == user_id,
                    UserMemory.memory_type.in_(["preference", "habit"])
                )
            ).order_by(desc(UserMemory.importance_score)).limit(10).all()
            
            return {
                "user_preferences": user.preferences or {},
                "stored_memories": [memory.content for memory in preferences]
            }
        finally:
            session.close()
    
    # Device Management
    def get_device(self, device_id: str) -> Optional[Device]:
        """Get device by ID"""
        session = self.get_session()
        try:
            return session.query(Device).filter_by(id=device_id).first()
        finally:
            session.close()
    
    def get_all_devices(self, active_only: bool = True) -> List[Device]:
        """Get all devices"""
        session = self.get_session()
        try:
            query = session.query(Device)
            if active_only:
                query = query.filter_by(is_active=True)
            return query.all()
        finally:
            session.close()
    
    def update_device_state(
        self, 
        device_id: str, 
        new_state: Dict, 
        user_id: str = None
    ) -> bool:
        """Update device state"""
        session = self.get_session()
        try:
            device = session.query(Device).filter_by(id=device_id).first()
            if not device:
                return False
            
            # Update device state - SQLAlchemy JSON fields need explicit assignment
            current_state = device.current_state.copy() if device.current_state else {}
            current_state.update(new_state)
            device.current_state = current_state  # Explicit assignment for SQLAlchemy to track changes
            device.last_updated = datetime.utcnow()
            
            session.commit()
            
            return True
        finally:
            session.close()
    
    def log_device_interaction(
        self,
        user_id: str,
        device_id: str,
        action: str,
        parameters: Dict = None,
        result: Dict = None,
        success: bool = True,
        conversation_id: str = None,
        error_message: str = None
    ) -> DeviceInteraction:
        """Log a device interaction"""
        session = self.get_session()
        try:
            interaction = DeviceInteraction(
                user_id=user_id,
                device_id=device_id,
                action=action,
                parameters=parameters or {},
                result=result or {},
                success=success,
                conversation_id=conversation_id,
                error_message=error_message
            )
            session.add(interaction)
            session.commit()
            session.refresh(interaction)
            return interaction
        finally:
            session.close()
    
    def get_device_usage_stats(
        self, 
        user_id: str = None, 
        device_id: str = None,
        days: int = 7
    ) -> List[Dict]:
        """Get device usage statistics"""
        session = self.get_session()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = session.query(DeviceInteraction).filter(
                DeviceInteraction.timestamp >= start_date
            )
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            if device_id:
                query = query.filter_by(device_id=device_id)
            
            interactions = query.all()
            
            # Group by device and action
            stats = {}
            for interaction in interactions:
                key = f"{interaction.device_id}_{interaction.action}"
                if key not in stats:
                    stats[key] = {
                        "device_id": interaction.device_id,
                        "action": interaction.action,
                        "count": 0,
                        "success_rate": 0.0,
                        "last_used": None
                    }
                
                stats[key]["count"] += 1
                if interaction.success:
                    stats[key]["success_rate"] += 1
                stats[key]["last_used"] = max(
                    stats[key]["last_used"] or interaction.timestamp,
                    interaction.timestamp
                )
            
            # Calculate success rates
            for stat in stats.values():
                stat["success_rate"] = stat["success_rate"] / stat["count"]
                if stat["last_used"]:
                    stat["last_used"] = stat["last_used"].isoformat()
            
            return list(stats.values())
        finally:
            session.close()
    
    # System Settings
    def get_system_setting(self, setting_id: str, default_value: Any = None) -> Any:
        """Get a system setting"""
        session = self.get_session()
        try:
            setting = session.query(SystemSettings).filter_by(id=setting_id).first()
            return setting.value if setting else default_value
        finally:
            session.close()
    
    def set_system_setting(self, setting_id: str, value: Any, description: str = None) -> bool:
        """Set a system setting"""
        session = self.get_session()
        try:
            setting = session.query(SystemSettings).filter_by(id=setting_id).first()
            if setting:
                setting.value = value
                setting.updated_at = datetime.utcnow()
                if description:
                    setting.description = description
            else:
                setting = SystemSettings(
                    id=setting_id,
                    value=value,
                    description=description
                )
                session.add(setting)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error setting system setting {setting_id}: {e}")
            return False
        finally:
            session.close()
    
    # Analytics and Reporting
    def get_user_statistics(self, user_id: str) -> Dict:
        """Get user usage statistics"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return {}
            
            # Count conversations
            conversation_count = session.query(Conversation).filter_by(
                user_id=user_id
            ).count()
            
            # Count messages
            message_count = session.query(Message).join(Conversation).filter(
                Conversation.user_id == user_id
            ).count()
            
            # Count device interactions
            interaction_count = session.query(DeviceInteraction).filter_by(
                user_id=user_id
            ).count()
            
            # Count memories
            memory_count = session.query(UserMemory).filter_by(
                user_id=user_id
            ).count()
            
            return {
                "user_id": user_id,
                "familiarity_score": user.familiarity_score,
                "conversation_count": conversation_count,
                "message_count": message_count,
                "device_interaction_count": interaction_count,
                "memory_count": memory_count,
                "member_since": user.created_at.isoformat() if user.created_at else None,
                "last_seen": user.last_seen.isoformat() if user.last_seen else None
            }
        finally:
            session.close()
    
    def get_system_statistics(self) -> Dict:
        """Get system-wide statistics"""
        session = self.get_session()
        try:
            user_count = session.query(User).filter_by(is_active=True).count()
            conversation_count = session.query(Conversation).count()
            active_conversation_count = session.query(Conversation).filter_by(
                is_active=True
            ).count()
            message_count = session.query(Message).count()
            device_count = session.query(Device).filter_by(is_active=True).count()
            
            return {
                "active_users": user_count,
                "total_conversations": conversation_count,
                "active_conversations": active_conversation_count,
                "total_messages": message_count,
                "active_devices": device_count,
                "generated_at": datetime.utcnow().isoformat()
            }
        finally:
            session.close()
    
    def initialize_default_data(self):
        """Initialize default data"""
        self.db_manager.init_default_data()
