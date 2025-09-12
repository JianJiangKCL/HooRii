"""
Database models for the Smart Home AI Assistant
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import json

@dataclass
class ConversationContext:
    """Manages state for a single conversation session"""
    conversation_id: str
    user_id: str
    familiarity_score: Optional[int] = None
    tone: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    conversation_history: List[Dict] = field(default_factory=list)
    cached_memories: List[Dict] = field(default_factory=list)
    device_states_cache: Dict = field(default_factory=dict)
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if conversation has expired"""
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)
    
    def update_activity(self):
        """Update activity timestamp and message count"""
        self.last_activity = datetime.now()
        self.message_count += 1

Base = declarative_base()

class User(Base):
    """User model for storing user profiles and preferences"""
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)  # For future auth implementation
    
    # AI Assistant specific fields
    familiarity_score = Column(Integer, default=25, nullable=False)  # 0-100
    preferred_tone = Column(String(20), default='polite')  # formal, polite, casual, intimate
    
    # User preferences
    preferences = Column(JSON, default=dict)  # Flexible preference storage
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("UserMemory", back_populates="user", cascade="all, delete-orphan")
    device_interactions = relationship("DeviceInteraction", back_populates="user")
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'familiarity_score': self.familiarity_score,
            'preferred_tone': self.preferred_tone,
            'preferences': self.preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'is_active': self.is_active
        }

class Conversation(Base):
    """Conversation sessions with context management"""
    __tablename__ = 'conversations'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # Conversation metadata
    title = Column(String(255))  # Auto-generated or user-set title
    start_time = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    message_count = Column(Integer, default=0)
    
    # Context data
    context_data = Column(JSON, default=dict)  # Cached memories, device states, etc.
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    @property
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if conversation has expired"""
        if not self.last_activity:
            return True
        return (datetime.utcnow() - self.last_activity).total_seconds() > (timeout_minutes * 60)
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
        self.message_count += 1
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'message_count': self.message_count,
            'is_active': self.is_active,
            'context_data': self.context_data
        }

class Message(Base):
    """Individual messages within conversations"""
    __tablename__ = 'messages'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey('conversations.id'), nullable=False)
    
    # Message content
    user_input = Column(Text, nullable=True)
    assistant_response = Column(Text, nullable=True)
    message_type = Column(String(50), default='chat')  # chat, system, error, etc.
    
    # Context
    tone_used = Column(String(20))
    intent_detected = Column(JSON)  # Store intent analysis results
    tools_used = Column(JSON, default=list)  # List of tools called (JSON array)
    
    # Langfuse integration
    langfuse_trace_id = Column(String, nullable=True)
    langfuse_observation_id = Column(String, nullable=True)
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Float, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'user_input': self.user_input,
            'assistant_response': self.assistant_response,
            'message_type': self.message_type,
            'tone_used': self.tone_used,
            'intent_detected': self.intent_detected,
            'tools_used': self.tools_used,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'processing_time_ms': self.processing_time_ms
        }

class UserMemory(Base):
    """User memories and preferences for personalization"""
    __tablename__ = 'user_memories'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # Memory content
    content = Column(Text, nullable=False)
    memory_type = Column(String(50), default='general')  # general, preference, habit, etc.
    keywords = Column(JSON, default=list)  # For quick searching (JSON array)
    
    # Embedding for semantic search (will implement later)
    embedding = Column(JSON, nullable=True)  # Store as JSON array for now
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)
    importance_score = Column(Float, default=1.0)  # 0.0 - 1.0
    
    # Source tracking
    source_conversation_id = Column(String, nullable=True)
    source_message_id = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="memories")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'memory_type': self.memory_type,
            'keywords': self.keywords,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'access_count': self.access_count,
            'importance_score': self.importance_score
        }

class Device(Base):
    """Smart home devices registry"""
    __tablename__ = 'devices'
    
    id = Column(String, primary_key=True)  # e.g., "living_room_lights"
    name = Column(String(255), nullable=False)
    device_type = Column(String(100), nullable=False)  # lights, tv, speaker, etc.
    room = Column(String(100), nullable=True)
    
    # Device capabilities
    supported_actions = Column(JSON, default=list)  # turn_on, turn_off, set_volume, etc. (JSON array)
    capabilities = Column(JSON, default=dict)  # brightness, color, channels, etc.
    
    # Current state
    current_state = Column(JSON, default=dict)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    requires_auth = Column(Boolean, default=False)
    min_familiarity_required = Column(Integer, default=40)
    
    # Relationships
    interactions = relationship("DeviceInteraction", back_populates="device")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'device_type': self.device_type,
            'room': self.room,
            'supported_actions': self.supported_actions,
            'capabilities': self.capabilities,
            'current_state': self.current_state,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'is_active': self.is_active,
            'requires_auth': self.requires_auth,
            'min_familiarity_required': self.min_familiarity_required
        }

class DeviceInteraction(Base):
    """Log of device interactions for analytics and learning"""
    __tablename__ = 'device_interactions'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    device_id = Column(String, ForeignKey('devices.id'), nullable=False)
    
    # Interaction details
    action = Column(String(100), nullable=False)
    parameters = Column(JSON, default=dict)
    result = Column(JSON, default=dict)  # Success/failure info
    
    # Context
    conversation_id = Column(String, nullable=True)
    message_id = Column(String, nullable=True)
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="device_interactions")
    device = relationship("Device", back_populates="interactions")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_id': self.device_id,
            'action': self.action,
            'parameters': self.parameters,
            'result': self.result,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'success': self.success,
            'error_message': self.error_message
        }

class SystemSettings(Base):
    """System-wide configuration settings"""
    __tablename__ = 'system_settings'
    
    id = Column(String, primary_key=True)
    value = Column(JSON)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Database connection and session management
class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all tables (be careful!)"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    def init_default_data(self):
        """Initialize default data"""
        session = self.get_session()
        try:
            # Create default devices
            default_devices = [
                {
                    'id': 'living_room_lights',
                    'name': '客厅灯',
                    'device_type': 'lights',
                    'room': 'living_room',
                    'supported_actions': ['turn_on', 'turn_off', 'set_brightness'],
                    'capabilities': {'brightness': {'min': 0, 'max': 100}},
                    'current_state': {'status': 'off', 'brightness': 0}
                },
                {
                    'id': 'tv',
                    'name': '电视',
                    'device_type': 'tv',
                    'room': 'living_room',
                    'supported_actions': ['turn_on', 'turn_off', 'set_channel', 'set_volume'],
                    'capabilities': {'volume': {'min': 0, 'max': 100}, 'channels': ['Netflix', 'YouTube', 'CCTV-1']},
                    'current_state': {'status': 'off', 'channel': '', 'volume': 50}
                },
                {
                    'id': 'soundbar',
                    'name': '音响',
                    'device_type': 'speaker',
                    'room': 'living_room',
                    'supported_actions': ['turn_on', 'turn_off', 'set_volume'],
                    'capabilities': {'volume': {'min': 0, 'max': 100}},
                    'current_state': {'status': 'off', 'volume': 50}
                }
            ]
            
            for device_data in default_devices:
                existing_device = session.query(Device).filter_by(id=device_data['id']).first()
                if not existing_device:
                    device = Device(**device_data)
                    session.add(device)
            
            # Create default system settings
            default_settings = [
                {'id': 'conversation_timeout_minutes', 'value': 30, 'description': '对话超时时间（分钟）'},
                {'id': 'default_familiarity_score', 'value': 25, 'description': '新用户默认熟悉度分数'},
                {'id': 'min_familiarity_for_hardware', 'value': 40, 'description': '控制硬件所需的最低熟悉度'},
                {'id': 'max_conversation_history', 'value': 100, 'description': '每个对话保存的最大消息数量'}
            ]
            
            for setting_data in default_settings:
                existing_setting = session.query(SystemSettings).filter_by(id=setting_data['id']).first()
                if not existing_setting:
                    setting = SystemSettings(**setting_data)
                    session.add(setting)
            
            session.commit()
            print("✅ Default data initialized successfully")
        except Exception as e:
            session.rollback()
            print(f"❌ Error initializing default data: {e}")
        finally:
            session.close()
