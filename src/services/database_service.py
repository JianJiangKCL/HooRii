"""
Database service layer for the Smart Home AI Assistant
Replaces the mock databases with real database operations
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, String

from ..models.database import (
    User, Conversation, Message, UserMemory, Device, UserDevice,
    DeviceInteraction, SystemSettings, DatabaseManager
)
from ..utils.config import Config

@dataclass
class UserInfo:
    """Simple data class to avoid SQLAlchemy session issues"""
    id: str
    username: str
    familiarity_score: int
    last_seen: datetime
    created_at: datetime

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
    def get_or_create_user(self, user_id: str, username: str = None, **kwargs) -> UserInfo:
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

            # Create UserInfo object to avoid session issues
            user_info = UserInfo(
                id=user.id,
                username=user.username,
                familiarity_score=user.familiarity_score,
                last_seen=user.last_seen,
                created_at=user.created_at
            )
            return user_info
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
    
    def get_user_metadata(self, user_id: str) -> dict:
        """Get user metadata safely for external use"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                return {
                    "interaction_count": user.interaction_count or 0,
                    "familiarity_score": user.familiarity_score,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_seen": user.last_seen.isoformat() if user.last_seen else None
                }
            return {}
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

    def get_recent_conversations_for_user(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Conversation]:
        """Get recent active conversations for a user"""
        session = self.get_session()
        try:
            conversations = session.query(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.is_active == True
                )
            ).order_by(desc(Conversation.last_activity)).limit(limit).all()

            return conversations
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


    def increment_user_interaction(self, user_id: str):
        """Increment user interaction count for familiarity scoring"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.interaction_count = (user.interaction_count or 0) + 1
                user.last_seen = datetime.utcnow()
                # Update familiarity score based on interactions
                if user.interaction_count <= 10:
                    user.familiarity_score = min(30, user.interaction_count * 3)
                elif user.interaction_count <= 30:
                    user.familiarity_score = min(60, 30 + (user.interaction_count - 10) * 1.5)
                else:
                    user.familiarity_score = min(100, 60 + (user.interaction_count - 30) * 0.8)
                session.commit()
        finally:
            session.close()

    # Enhanced User Management
    def update_user(self, user_id: str, **updates) -> bool:
        """Update user information"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return False
            
            # Update allowed fields
            allowed_fields = ['username', 'email', 'familiarity_score', 'preferred_tone', 'preferences', 'is_active']
            for field, value in updates.items():
                if field in allowed_fields and value is not None:
                    setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating user {user_id}: {e}")
            return False
        finally:
            session.close()

    def delete_user(self, user_id: str, soft_delete: bool = True) -> bool:
        """Delete user (soft delete by default)"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return False
            
            if soft_delete:
                user.is_active = False
                user.updated_at = datetime.utcnow()
            else:
                session.delete(user)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error deleting user {user_id}: {e}")
            return False
        finally:
            session.close()

    def get_all_users(self, active_only: bool = True, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with pagination"""
        session = self.get_session()
        try:
            query = session.query(User)
            if active_only:
                query = query.filter_by(is_active=True)
            return query.offset(offset).limit(limit).all()
        finally:
            session.close()

    # Enhanced Device Management
    def create_device(self, device_data: Dict) -> Optional[Device]:
        """Create a new device"""
        session = self.get_session()
        try:
            # Check if device already exists
            existing = session.query(Device).filter_by(id=device_data['id']).first()
            if existing:
                return None
            
            device = Device(**device_data)
            session.add(device)
            session.commit()
            session.refresh(device)
            return device
        except Exception as e:
            session.rollback()
            print(f"Error creating device: {e}")
            return None
        finally:
            session.close()

    def update_device(self, device_id: str, **updates) -> bool:
        """Update device information"""
        session = self.get_session()
        try:
            device = session.query(Device).filter_by(id=device_id).first()
            if not device:
                return False
            
            # Update allowed fields
            allowed_fields = ['name', 'device_type', 'room', 'supported_actions', 'capabilities', 
                            'current_state', 'min_familiarity_required', 'requires_auth', 'is_active']
            for field, value in updates.items():
                if field in allowed_fields and value is not None:
                    setattr(device, field, value)
            
            device.last_updated = datetime.utcnow()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating device {device_id}: {e}")
            return False
        finally:
            session.close()

    def delete_device(self, device_id: str, soft_delete: bool = True) -> bool:
        """Delete device (soft delete by default)"""
        session = self.get_session()
        try:
            device = session.query(Device).filter_by(id=device_id).first()
            if not device:
                return False
            
            if soft_delete:
                device.is_active = False
                device.last_updated = datetime.utcnow()
            else:
                session.delete(device)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error deleting device {device_id}: {e}")
            return False
        finally:
            session.close()

    def get_devices_by_room(self, room: str, active_only: bool = True) -> List[Device]:
        """Get devices by room"""
        session = self.get_session()
        try:
            query = session.query(Device).filter_by(room=room)
            if active_only:
                query = query.filter_by(is_active=True)
            return query.all()
        finally:
            session.close()

    def get_devices_by_type(self, device_type: str, active_only: bool = True) -> List[Device]:
        """Get devices by type"""
        session = self.get_session()
        try:
            query = session.query(Device).filter_by(device_type=device_type)
            if active_only:
                query = query.filter_by(is_active=True)
            return query.all()
        finally:
            session.close()

    # Bulk Operations
    def bulk_create_users(self, users_data: List[Dict]) -> Dict[str, Any]:
        """Bulk create users"""
        session = self.get_session()
        results = {"created": 0, "errors": [], "users": []}
        
        try:
            for user_data in users_data:
                try:
                    # Check if user already exists
                    existing = session.query(User).filter_by(id=user_data.get('username', '')).first()
                    if existing:
                        results["errors"].append(f"User {user_data.get('username')} already exists")
                        continue
                    
                    user = User(
                        id=user_data['username'],
                        username=user_data['username'],
                        email=user_data.get('email'),
                        familiarity_score=user_data.get('familiarity_score', 25)
                    )
                    session.add(user)
                    results["created"] += 1
                    results["users"].append(user_data['username'])
                except Exception as e:
                    results["errors"].append(f"Error creating user {user_data.get('username', 'unknown')}: {e}")
            
            session.commit()
        except Exception as e:
            session.rollback()
            results["errors"].append(f"Bulk operation failed: {e}")
        finally:
            session.close()
        
        return results

    def bulk_create_devices(self, devices_data: List[Dict]) -> Dict[str, Any]:
        """Bulk create devices"""
        session = self.get_session()
        results = {"created": 0, "errors": [], "devices": []}
        
        try:
            for device_data in devices_data:
                try:
                    # Check if device already exists
                    existing = session.query(Device).filter_by(id=device_data['id']).first()
                    if existing:
                        results["errors"].append(f"Device {device_data['id']} already exists")
                        continue
                    
                    device = Device(**device_data)
                    session.add(device)
                    results["created"] += 1
                    results["devices"].append(device_data['id'])
                except Exception as e:
                    results["errors"].append(f"Error creating device {device_data.get('id', 'unknown')}: {e}")
            
            session.commit()
        except Exception as e:
            session.rollback()
            results["errors"].append(f"Bulk operation failed: {e}")
        finally:
            session.close()
        
        return results
   # User Device Management
    def get_user_devices(self, user_id: str, active_only: bool = True) -> List:
        """Get all devices for a user"""
        from ..models.database import UserDevice
        session = self.get_session()
        try:
            query = session.query(UserDevice).filter_by(user_id=user_id)
            if active_only:
                query = query.filter_by(is_accessible=True)
            user_devices = query.all()
            # Convert to dicts to avoid session issues
            result = []
            for ud in user_devices:
                result.append(ud)
            return result
        finally:
            session.close()

    def get_user_device(self, user_id: str, device_id: str):
        """Get a specific user device configuration"""
        from ..models.database import UserDevice
        session = self.get_session()
        try:
            return session.query(UserDevice).filter_by(
                user_id=user_id, 
                device_id=device_id
            ).first()
        finally:
            session.close()

    def add_user_device(
        self, 
        user_id: str, 
        device_id: str,
        custom_name: str = None,
        is_favorite: bool = False,
        is_accessible: bool = True,
        min_familiarity_required: int = None,
        custom_permissions: Dict = None,
        allowed_actions: List[str] = None,
        user_preferences: Dict = None,
        quick_actions: List[str] = None
    ):
        """Add a device to user's device list"""
        from ..models.database import UserDevice
        session = self.get_session()
        try:
            # Check if already exists
            existing = session.query(UserDevice).filter_by(
                user_id=user_id,
                device_id=device_id
            ).first()
            
            if existing:
                return None
            
            user_device = UserDevice(
                user_id=user_id,
                device_id=device_id,
                custom_name=custom_name,
                is_favorite=is_favorite,
                is_accessible=is_accessible,
                min_familiarity_required=min_familiarity_required,
                custom_permissions=custom_permissions or {},
                allowed_actions=allowed_actions or [],
                user_preferences=user_preferences or {},
                quick_actions=quick_actions or []
            )
            
            session.add(user_device)
            session.commit()
            session.refresh(user_device)
            return user_device
        except Exception as e:
            session.rollback()
            print(f"Error adding user device: {e}")
            return None
        finally:
            session.close()

    def update_user_device(self, user_id: str, device_id: str, **updates) -> bool:
        """Update user device configuration"""
        from ..models.database import UserDevice
        session = self.get_session()
        try:
            user_device = session.query(UserDevice).filter_by(
                user_id=user_id,
                device_id=device_id
            ).first()
            
            if not user_device:
                return False
            
            # Update allowed fields
            allowed_fields = ['custom_name', 'is_favorite', 'is_accessible', 
                            'min_familiarity_required', 'custom_permissions',
                            'allowed_actions', 'user_preferences', 'quick_actions']
            for field, value in updates.items():
                if field in allowed_fields and value is not None:
                    setattr(user_device, field, value)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating user device: {e}")
            return False
        finally:
            session.close()

    def remove_user_device(self, user_id: str, device_id: str) -> bool:
        """Remove a device from user's device list"""
        from ..models.database import UserDevice
        session = self.get_session()
        try:
            user_device = session.query(UserDevice).filter_by(
                user_id=user_id,
                device_id=device_id
            ).first()
            
            if not user_device:
                return False
            
            session.delete(user_device)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error removing user device: {e}")
            return False
        finally:
            session.close()

    def get_user_favorite_devices(self, user_id: str):
        """Get user's favorite devices"""
        from ..models.database import UserDevice
        session = self.get_session()
        try:
            user_devices = session.query(UserDevice).filter_by(
                user_id=user_id,
                is_favorite=True,
                is_accessible=True
            ).all()
            result = []
            for ud in user_devices:
                result.append(ud)
            return result
        finally:
            session.close()

    def import_user_devices(
        self, 
        user_id: str, 
        devices_data: List[Dict],
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Bulk import user devices configuration"""
        from ..models.database import UserDevice
        session = self.get_session()
        results = {"imported": 0, "updated": 0, "errors": [], "devices": []}
        
        try:
            for device_data in devices_data:
                try:
                    device_id = device_data.get('device_id')
                    if not device_id:
                        results["errors"].append("Missing device_id in device data")
                        continue
                    
                    existing = session.query(UserDevice).filter_by(
                        user_id=user_id,
                        device_id=device_id
                    ).first()
                    
                    if existing and not overwrite_existing:
                        results["errors"].append(f"User device {device_id} already exists, skipped")
                        continue
                    
                    if existing and overwrite_existing:
                        # Update existing
                        for key, value in device_data.items():
                            if key != 'device_id' and hasattr(existing, key):
                                setattr(existing, key, value)
                        results["updated"] += 1
                        results["devices"].append(device_id)
                    else:
                        # Create new
                        user_device = UserDevice(
                            user_id=user_id,
                            device_id=device_id,
                            custom_name=device_data.get('custom_name'),
                            is_favorite=device_data.get('is_favorite', False),
                            is_accessible=device_data.get('is_accessible', True),
                            min_familiarity_required=device_data.get('min_familiarity_required'),
                            custom_permissions=device_data.get('custom_permissions', {}),
                            allowed_actions=device_data.get('allowed_actions', []),
                            user_preferences=device_data.get('user_preferences', {}),
                            quick_actions=device_data.get('quick_actions', [])
                        )
                        session.add(user_device)
                        results["imported"] += 1
                        results["devices"].append(device_id)
                        
                except Exception as e:
                    results["errors"].append(f"Error processing device {device_data.get('device_id', 'unknown')}: {e}")
            
            session.commit()
        except Exception as e:
            session.rollback()
            results["errors"].append(f"Bulk import failed: {e}")
        finally:
            session.close()
        
        return results

    def export_user_devices(self, user_id: str) -> Dict[str, Any]:
        """Export user devices configuration"""
        from ..models.database import UserDevice
        session = self.get_session()
        try:
            user_devices = session.query(UserDevice).filter_by(user_id=user_id).all()
            
            devices_data = []
            for ud in user_devices:
                device_dict = {
                    "device_id": ud.device_id,
                    "custom_name": ud.custom_name,
                    "is_favorite": ud.is_favorite,
                    "is_accessible": ud.is_accessible,
                    "min_familiarity_required": ud.min_familiarity_required,
                    "custom_permissions": ud.custom_permissions or {},
                    "allowed_actions": ud.allowed_actions or [],
                    "user_preferences": ud.user_preferences or {},
                    "quick_actions": ud.quick_actions or [],
                    "added_at": ud.added_at.isoformat() if ud.added_at else None,
                    "last_used": ud.last_used.isoformat() if ud.last_used else None,
                    "usage_count": ud.usage_count or 0
                }
                devices_data.append(device_dict)
            
            return {
                "user_id": user_id,
                "devices": devices_data,
                "export_info": {
                    "total_count": len(devices_data),
                    "export_time": datetime.utcnow().isoformat()
                }
            }
        finally:
            session.close()
