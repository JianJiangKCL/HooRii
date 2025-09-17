"""
RESTful API for the Smart Home AI Assistant
"""
import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

from config import load_config, Config
from main import HomeAITaskPlanner
from database_service import DatabaseService
from models import User, Conversation, Device

# Initialize FastAPI app
app = FastAPI(
    title="Smart Home AI Assistant API",
    description="智能陪伴家居控制系统 API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Global instances (initialized on startup)
config: Config = None
planner: HomeAITaskPlanner = None
db_service: DatabaseService = None

# Pydantic models for API
class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=80)
    email: Optional[str] = None
    familiarity_score: Optional[int] = Field(None, ge=0, le=100)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    user_id: str
    familiarity_score: int
    message_count: int
    processing_time_ms: float
    timestamp: datetime

class DeviceControlRequest(BaseModel):
    device_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    parameters: Optional[Dict] = Field(default_factory=dict)
    user_id: str = Field(..., min_length=1)

class DeviceControlResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    device_state: Optional[Dict] = None
    timestamp: datetime

class UserMemoryRequest(BaseModel):
    content: str = Field(..., min_length=1)
    memory_type: Optional[str] = "general"
    keywords: Optional[List[str]] = Field(default_factory=list)
    importance_score: Optional[float] = Field(1.0, ge=0.0, le=1.0)

# New models for comprehensive user/device management
class UserUpdateRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=80)
    email: Optional[str] = None
    familiarity_score: Optional[int] = Field(None, ge=0, le=100)
    preferred_tone: Optional[str] = Field(None, regex="^(formal|polite|casual|intimate)$")
    preferences: Optional[Dict] = None
    is_active: Optional[bool] = None

class DeviceCreateRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    device_type: str = Field(..., min_length=1, max_length=100)
    room: Optional[str] = Field(None, max_length=100)
    supported_actions: Optional[List[str]] = Field(default_factory=list)
    capabilities: Optional[Dict] = Field(default_factory=dict)
    min_familiarity_required: Optional[int] = Field(40, ge=0, le=100)
    requires_auth: Optional[bool] = False

class DeviceUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    device_type: Optional[str] = Field(None, min_length=1, max_length=100)
    room: Optional[str] = Field(None, max_length=100)
    supported_actions: Optional[List[str]] = None
    capabilities: Optional[Dict] = None
    current_state: Optional[Dict] = None
    min_familiarity_required: Optional[int] = Field(None, ge=0, le=100)
    requires_auth: Optional[bool] = None
    is_active: Optional[bool] = None

class BulkUserImportRequest(BaseModel):
    users: List[UserCreateRequest] = Field(..., min_items=1, max_items=100)

class BulkDeviceImportRequest(BaseModel):
    devices: List[DeviceCreateRequest] = Field(..., min_items=1, max_items=50)

# JSON Import/Export models
class UserJsonImportRequest(BaseModel):
    users: List[Dict] = Field(..., min_items=1, max_items=1000, description="JSON格式的用户数据列表")
    overwrite_existing: Optional[bool] = Field(False, description="是否覆盖已存在的用户")

class DeviceJsonImportRequest(BaseModel):
    devices: List[Dict] = Field(..., min_items=1, max_items=500, description="JSON格式的设备数据列表")
    overwrite_existing: Optional[bool] = Field(False, description="是否覆盖已存在的设备")

class JsonExportRequest(BaseModel):
    include_inactive: Optional[bool] = Field(False, description="是否包含非活跃的记录")
    user_ids: Optional[List[str]] = Field(None, description="指定导出的用户ID列表，为空则导出所有用户")
    device_ids: Optional[List[str]] = Field(None, description="指定导出的设备ID列表，为空则导出所有设备")

# User Device Management models
class UserDeviceAddRequest(BaseModel):
    device_id: str = Field(..., description="要添加的设备ID")
    custom_name: Optional[str] = Field(None, description="用户自定义设备名称")
    is_favorite: Optional[bool] = Field(False, description="是否设为收藏")
    is_accessible: Optional[bool] = Field(True, description="用户是否可以访问此设备")
    min_familiarity_required: Optional[int] = Field(None, ge=0, le=100, description="覆盖默认熟悉度要求")
    custom_permissions: Optional[Dict] = Field(default_factory=dict, description="自定义权限设置")
    allowed_actions: Optional[List[str]] = Field(None, description="允许的操作列表")
    user_preferences: Optional[Dict] = Field(default_factory=dict, description="用户偏好设置")
    quick_actions: Optional[List[str]] = Field(default_factory=list, description="快捷操作列表")

class UserDeviceUpdateRequest(BaseModel):
    custom_name: Optional[str] = Field(None, description="用户自定义设备名称")
    is_favorite: Optional[bool] = Field(None, description="是否设为收藏")
    is_accessible: Optional[bool] = Field(None, description="用户是否可以访问此设备")
    min_familiarity_required: Optional[int] = Field(None, ge=0, le=100, description="熟悉度要求")
    custom_permissions: Optional[Dict] = Field(None, description="自定义权限设置")
    allowed_actions: Optional[List[str]] = Field(None, description="允许的操作列表")
    user_preferences: Optional[Dict] = Field(None, description="用户偏好设置")
    quick_actions: Optional[List[str]] = Field(None, description="快捷操作列表")

class UserDeviceImportRequest(BaseModel):
    devices: List[Dict] = Field(..., min_items=1, max_items=100, description="用户设备配置列表")
    overwrite_existing: Optional[bool] = Field(False, description="是否覆盖已存在的设备配置")

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    global config, planner, db_service
    try:
        config = load_config()
        planner = HomeAITaskPlanner(config)
        db_service = planner.db_service
        print("🚀 API server started successfully")
    except Exception as e:
        print(f"❌ Failed to initialize API server: {e}")
        raise

@app.on_event("shutdown")
async def shutdown():
    print("👋 API server shutting down")

# Dependency functions
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Simple token-based authentication (placeholder)"""
    # For now, just return a default user ID
    # In production, implement proper JWT validation
    if credentials and credentials.credentials:
        # Extract user_id from token (implement proper JWT decoding)
        return credentials.credentials  # Placeholder
    return "default_user"  # Default for development

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# User management endpoints
@app.post("/users", response_model=Dict)
async def create_user(user_data: UserCreateRequest):
    """Create a new user"""
    try:
        user = db_service.get_or_create_user(
            user_id=user_data.username,  # Use username as ID for simplicity
            username=user_data.username,
            email=user_data.email
        )
        
        if user_data.familiarity_score is not None:
            db_service.update_user_familiarity(user.id, user_data.familiarity_score)
        
        return {
            "success": True,
            "user": user.to_dict(),
            "message": f"用户 {user_data.username} 创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get user information"""
    try:
        user = db_service.get_or_create_user(user_id)
        stats = db_service.get_user_statistics(user_id)
        return {
            "user": user.to_dict(),
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")

@app.put("/users/{user_id}/familiarity")
async def update_familiarity(user_id: str, score: int = Body(..., ge=0, le=100)):
    """Update user familiarity score"""
    try:
        success = db_service.update_user_familiarity(user_id, score)
        if success:
            return {"success": True, "message": f"用户 {user_id} 熟悉度已更新为 {score}"}
        else:
            raise HTTPException(status_code=404, detail="用户不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新熟悉度失败: {str(e)}")

@app.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdateRequest):
    """Update user information"""
    try:
        updates = user_data.dict(exclude_unset=True)
        success = db_service.update_user(user_id, **updates)
        
        if success:
            user = db_service.get_or_create_user(user_id)
            return {
                "success": True,
                "user": user.to_dict(),
                "message": f"用户 {user_id} 信息已更新"
            }
        else:
            raise HTTPException(status_code=404, detail="用户不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新用户失败: {str(e)}")

@app.delete("/users/{user_id}")
async def delete_user(user_id: str, hard_delete: bool = Query(False)):
    """Delete user (soft delete by default)"""
    try:
        success = db_service.delete_user(user_id, soft_delete=not hard_delete)
        if success:
            delete_type = "永久删除" if hard_delete else "停用"
            return {"success": True, "message": f"用户 {user_id} 已{delete_type}"}
        else:
            raise HTTPException(status_code=404, detail="用户不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")

@app.get("/users")
async def list_all_users(
    active_only: bool = Query(True),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all users with pagination"""
    try:
        users = db_service.get_all_users(active_only=active_only, limit=limit, offset=offset)
        return {
            "users": [user.to_dict() for user in users],
            "count": len(users),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")

@app.post("/users/bulk")
async def bulk_create_users(request: BulkUserImportRequest):
    """Bulk create users"""
    try:
        users_data = [user.dict() for user in request.users]
        results = db_service.bulk_create_users(users_data)
        
        return {
            "success": results["created"] > 0,
            "created_count": results["created"],
            "created_users": results["users"],
            "errors": results["errors"],
            "message": f"成功创建 {results['created']} 个用户"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量创建用户失败: {str(e)}")

# JSON Import/Export endpoints
@app.post("/users/import/json")
async def import_users_json(request: UserJsonImportRequest):
    """
    从JSON导入用户数据
    
    JSON格式要求:
    {
        "users": [
            {
                "id": "user_001",                    // 用户ID (必填)
                "username": "张三",                  // 用户名 (必填)
                "email": "zhangsan@example.com",     // 邮箱 (可选)
                "familiarity_score": 75,             // 熟悉度分数 0-100 (可选，默认25)
                "preferred_tone": "casual",          // 语调偏好: formal/polite/casual/intimate (可选，默认polite)
                "preferences": {                     // 用户偏好设置 (可选)
                    "theme": "dark",
                    "language": "zh-CN"
                },
                "is_active": true                    // 是否活跃 (可选，默认true)
            }
        ],
        "overwrite_existing": false                  // 是否覆盖已存在的用户 (可选，默认false)
    }
    """
    try:
        results = {
            "imported": 0,
            "updated": 0,
            "errors": [],
            "users": []
        }
        
        session = db_service.get_session()
        try:
            for user_data in request.users:
                try:
                    # 验证必填字段
                    if 'id' not in user_data or 'username' not in user_data:
                        results["errors"].append("用户数据缺少必填字段 id 或 username")
                        continue
                    
                    user_id = user_data['id']
                    existing_user = session.query(User).filter_by(id=user_id).first()
                    
                    if existing_user and not request.overwrite_existing:
                        results["errors"].append(f"用户 {user_id} 已存在，跳过")
                        continue
                    
                    if existing_user and request.overwrite_existing:
                        # 更新现有用户
                        for key, value in user_data.items():
                            if key in ['username', 'email', 'familiarity_score', 'preferred_tone', 'preferences', 'is_active']:
                                setattr(existing_user, key, value)
                        existing_user.updated_at = datetime.utcnow()
                        results["updated"] += 1
                        results["users"].append(user_id)
                    else:
                        # 创建新用户
                        new_user = User(
                            id=user_id,
                            username=user_data['username'],
                            email=user_data.get('email'),
                            familiarity_score=user_data.get('familiarity_score', 25),
                            preferred_tone=user_data.get('preferred_tone', 'polite'),
                            preferences=user_data.get('preferences', {}),
                            is_active=user_data.get('is_active', True)
                        )
                        session.add(new_user)
                        results["imported"] += 1
                        results["users"].append(user_id)
                        
                except Exception as e:
                    results["errors"].append(f"处理用户 {user_data.get('id', 'unknown')} 时出错: {str(e)}")
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            results["errors"].append(f"批量导入失败: {str(e)}")
        finally:
            session.close()
        
        return {
            "success": results["imported"] > 0 or results["updated"] > 0,
            "imported_count": results["imported"],
            "updated_count": results["updated"],
            "processed_users": results["users"],
            "errors": results["errors"],
            "message": f"成功导入 {results['imported']} 个用户，更新 {results['updated']} 个用户"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JSON导入失败: {str(e)}")

@app.post("/users/export/json")
async def export_users_json(request: JsonExportRequest = None):
    """
    导出用户数据为JSON格式
    
    返回格式:
    {
        "users": [
            {
                "id": "user_001",
                "username": "张三",
                "email": "zhangsan@example.com",
                "familiarity_score": 75,
                "preferred_tone": "casual",
                "preferences": {"theme": "dark"},
                "interaction_count": 150,
                "is_active": true,
                "created_at": "2025-01-13T10:30:00Z",
                "updated_at": "2025-01-13T15:45:00Z",
                "last_seen": "2025-01-13T16:00:00Z"
            }
        ],
        "export_info": {
            "total_count": 1,
            "export_time": "2025-01-13T16:05:00Z",
            "include_inactive": false
        }
    }
    """
    try:
        if request is None:
            request = JsonExportRequest()
        
        session = db_service.get_session()
        try:
            query = session.query(User)
            
            # 过滤条件
            if not request.include_inactive:
                query = query.filter_by(is_active=True)
            
            if request.user_ids:
                query = query.filter(User.id.in_(request.user_ids))
            
            users = query.all()
            
            # 转换为JSON格式
            users_data = []
            for user in users:
                user_dict = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "familiarity_score": user.familiarity_score,
                    "preferred_tone": user.preferred_tone,
                    "preferences": user.preferences or {},
                    "interaction_count": user.interaction_count or 0,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                    "last_seen": user.last_seen.isoformat() if user.last_seen else None
                }
                users_data.append(user_dict)
            
            return {
                "users": users_data,
                "export_info": {
                    "total_count": len(users_data),
                    "export_time": datetime.utcnow().isoformat(),
                    "include_inactive": request.include_inactive,
                    "filtered_user_ids": request.user_ids
                }
            }
            
        finally:
            session.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JSON导出失败: {str(e)}")

@app.post("/devices/import/json")
async def import_devices_json(request: DeviceJsonImportRequest):
    """
    从JSON导入设备数据
    
    JSON格式要求:
    {
        "devices": [
            {
                "id": "living_room_light_001",      // 设备ID (必填)
                "name": "客厅主灯",                  // 设备名称 (必填)
                "device_type": "lights",             // 设备类型 (必填): lights/tv/speaker/air_conditioner/curtains/other
                "room": "客厅",                      // 房间 (可选)
                "supported_actions": [               // 支持的操作 (可选，会根据设备类型自动设置)
                    "turn_on", "turn_off", "set_brightness"
                ],
                "capabilities": {                    // 设备能力 (可选，会根据设备类型自动设置)
                    "brightness": {"min": 0, "max": 100}
                },
                "current_state": {                   // 当前状态 (可选，默认为off状态)
                    "status": "off",
                    "brightness": 0
                },
                "min_familiarity_required": 30,     // 所需最低熟悉度 (可选，默认40)
                "requires_auth": false,             // 是否需要认证 (可选，默认false)
                "is_active": true                   // 是否活跃 (可选，默认true)
            }
        ],
        "overwrite_existing": false                 // 是否覆盖已存在的设备 (可选，默认false)
    }
    """
    try:
        results = {
            "imported": 0,
            "updated": 0,
            "errors": [],
            "devices": []
        }
        
        session = db_service.get_session()
        try:
            for device_data in request.devices:
                try:
                    # 验证必填字段
                    if 'id' not in device_data or 'name' not in device_data or 'device_type' not in device_data:
                        results["errors"].append("设备数据缺少必填字段 id、name 或 device_type")
                        continue
                    
                    device_id = device_data['id']
                    existing_device = session.query(Device).filter_by(id=device_id).first()
                    
                    if existing_device and not request.overwrite_existing:
                        results["errors"].append(f"设备 {device_id} 已存在，跳过")
                        continue
                    
                    # 设置默认值
                    device_type = device_data['device_type']
                    
                    if 'supported_actions' not in device_data or not device_data['supported_actions']:
                        if device_type == "lights":
                            device_data['supported_actions'] = ["turn_on", "turn_off", "set_brightness"]
                        elif device_type == "tv":
                            device_data['supported_actions'] = ["turn_on", "turn_off", "set_volume", "set_channel"]
                        elif device_type == "speaker":
                            device_data['supported_actions'] = ["turn_on", "turn_off", "set_volume"]
                        else:
                            device_data['supported_actions'] = ["turn_on", "turn_off"]
                    
                    if 'capabilities' not in device_data or not device_data['capabilities']:
                        if device_type == "lights":
                            device_data['capabilities'] = {"brightness": {"min": 0, "max": 100}}
                        elif device_type in ["tv", "speaker"]:
                            device_data['capabilities'] = {"volume": {"min": 0, "max": 100}}
                        else:
                            device_data['capabilities'] = {}
                    
                    if 'current_state' not in device_data:
                        device_data['current_state'] = {"status": "off"}
                    
                    if existing_device and request.overwrite_existing:
                        # 更新现有设备
                        for key, value in device_data.items():
                            if key in ['name', 'device_type', 'room', 'supported_actions', 'capabilities', 
                                     'current_state', 'min_familiarity_required', 'requires_auth', 'is_active']:
                                setattr(existing_device, key, value)
                        existing_device.last_updated = datetime.utcnow()
                        results["updated"] += 1
                        results["devices"].append(device_id)
                    else:
                        # 创建新设备
                        new_device = Device(
                            id=device_id,
                            name=device_data['name'],
                            device_type=device_data['device_type'],
                            room=device_data.get('room'),
                            supported_actions=device_data['supported_actions'],
                            capabilities=device_data['capabilities'],
                            current_state=device_data['current_state'],
                            min_familiarity_required=device_data.get('min_familiarity_required', 40),
                            requires_auth=device_data.get('requires_auth', False),
                            is_active=device_data.get('is_active', True)
                        )
                        session.add(new_device)
                        results["imported"] += 1
                        results["devices"].append(device_id)
                        
                except Exception as e:
                    results["errors"].append(f"处理设备 {device_data.get('id', 'unknown')} 时出错: {str(e)}")
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            results["errors"].append(f"批量导入失败: {str(e)}")
        finally:
            session.close()
        
        return {
            "success": results["imported"] > 0 or results["updated"] > 0,
            "imported_count": results["imported"],
            "updated_count": results["updated"],
            "processed_devices": results["devices"],
            "errors": results["errors"],
            "message": f"成功导入 {results['imported']} 个设备，更新 {results['updated']} 个设备"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JSON导入失败: {str(e)}")

@app.post("/devices/export/json")
async def export_devices_json(request: JsonExportRequest = None):
    """
    导出设备数据为JSON格式
    
    返回格式:
    {
        "devices": [
            {
                "id": "living_room_light_001",
                "name": "客厅主灯",
                "device_type": "lights",
                "room": "客厅",
                "supported_actions": ["turn_on", "turn_off", "set_brightness"],
                "capabilities": {"brightness": {"min": 0, "max": 100}},
                "current_state": {"status": "off", "brightness": 0},
                "min_familiarity_required": 30,
                "requires_auth": false,
                "is_active": true,
                "last_updated": "2025-01-13T16:00:00Z"
            }
        ],
        "export_info": {
            "total_count": 1,
            "export_time": "2025-01-13T16:05:00Z",
            "include_inactive": false
        }
    }
    """
    try:
        if request is None:
            request = JsonExportRequest()
        
        session = db_service.get_session()
        try:
            query = session.query(Device)
            
            # 过滤条件
            if not request.include_inactive:
                query = query.filter_by(is_active=True)
            
            if request.device_ids:
                query = query.filter(Device.id.in_(request.device_ids))
            
            devices = query.all()
            
            # 转换为JSON格式
            devices_data = []
            for device in devices:
                device_dict = {
                    "id": device.id,
                    "name": device.name,
                    "device_type": device.device_type,
                    "room": device.room,
                    "supported_actions": device.supported_actions or [],
                    "capabilities": device.capabilities or {},
                    "current_state": device.current_state or {},
                    "min_familiarity_required": device.min_familiarity_required,
                    "requires_auth": device.requires_auth,
                    "is_active": device.is_active,
                    "last_updated": device.last_updated.isoformat() if device.last_updated else None
                }
                devices_data.append(device_dict)
            
            return {
                "devices": devices_data,
                "export_info": {
                    "total_count": len(devices_data),
                    "export_time": datetime.utcnow().isoformat(),
                    "include_inactive": request.include_inactive,
                    "filtered_device_ids": request.device_ids
                }
            }
            
        finally:
            session.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JSON导出失败: {str(e)}")

# User Device Management endpoints
@app.get("/users/{user_id}/devices")
async def get_user_devices(user_id: str, active_only: bool = Query(True)):
    """
    获取用户的设备列表
    
    返回用户可访问的所有设备，包含个性化配置
    """
    try:
        user_devices = db_service.get_user_devices(user_id, active_only=active_only)
        
        devices_data = []
        for ud in user_devices:
            device_info = ud.to_dict()
            devices_data.append(device_info)
        
        return {
            "user_id": user_id,
            "devices": devices_data,
            "count": len(devices_data),
            "active_only": active_only
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户设备列表失败: {str(e)}")

@app.post("/users/{user_id}/devices")
async def add_user_device(user_id: str, request: UserDeviceAddRequest):
    """
    为用户添加设备
    
    将指定设备添加到用户的个人设备列表中，可设置个性化配置
    """
    try:
        # 检查设备是否存在
        device = db_service.get_device(request.device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"设备 {request.device_id} 不存在")
        
        # 添加用户设备关系
        user_device = db_service.add_user_device(
            user_id=user_id,
            device_id=request.device_id,
            custom_name=request.custom_name,
            is_favorite=request.is_favorite,
            is_accessible=request.is_accessible,
            min_familiarity_required=request.min_familiarity_required,
            custom_permissions=request.custom_permissions,
            allowed_actions=request.allowed_actions or device.supported_actions,
            user_preferences=request.user_preferences,
            quick_actions=request.quick_actions
        )
        
        if user_device:
            return {
                "success": True,
                "user_device": user_device.to_dict(),
                "message": f"设备 {request.device_id} 已添加到用户 {user_id} 的设备列表"
            }
        else:
            raise HTTPException(status_code=409, detail="设备已存在于用户设备列表中")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加用户设备失败: {str(e)}")

@app.get("/users/{user_id}/devices/{device_id}")
async def get_user_device(user_id: str, device_id: str):
    """
    获取用户特定设备的配置
    """
    try:
        user_device = db_service.get_user_device(user_id, device_id)
        if not user_device:
            raise HTTPException(status_code=404, detail=f"用户 {user_id} 没有设备 {device_id}")
        
        return user_device.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户设备配置失败: {str(e)}")

@app.put("/users/{user_id}/devices/{device_id}")
async def update_user_device(user_id: str, device_id: str, request: UserDeviceUpdateRequest):
    """
    更新用户设备配置
    """
    try:
        updates = request.dict(exclude_unset=True)
        success = db_service.update_user_device(user_id, device_id, **updates)
        
        if success:
            user_device = db_service.get_user_device(user_id, device_id)
            return {
                "success": True,
                "user_device": user_device.to_dict(),
                "message": f"用户 {user_id} 的设备 {device_id} 配置已更新"
            }
        else:
            raise HTTPException(status_code=404, detail=f"用户 {user_id} 没有设备 {device_id}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新用户设备配置失败: {str(e)}")

@app.delete("/users/{user_id}/devices/{device_id}")
async def remove_user_device(user_id: str, device_id: str):
    """
    从用户设备列表中移除设备
    """
    try:
        success = db_service.remove_user_device(user_id, device_id)
        
        if success:
            return {
                "success": True,
                "message": f"设备 {device_id} 已从用户 {user_id} 的设备列表中移除"
            }
        else:
            raise HTTPException(status_code=404, detail=f"用户 {user_id} 没有设备 {device_id}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除用户设备失败: {str(e)}")

@app.get("/users/{user_id}/devices/favorites")
async def get_user_favorite_devices(user_id: str):
    """
    获取用户收藏的设备列表
    """
    try:
        favorite_devices = db_service.get_user_favorite_devices(user_id)
        
        devices_data = []
        for ud in favorite_devices:
            device_info = ud.to_dict()
            devices_data.append(device_info)
        
        return {
            "user_id": user_id,
            "favorite_devices": devices_data,
            "count": len(devices_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户收藏设备失败: {str(e)}")

@app.post("/users/{user_id}/devices/import")
async def import_user_devices(user_id: str, request: UserDeviceImportRequest):
    """
    批量导入用户设备配置
    
    JSON格式要求:
    {
        "devices": [
            {
                "device_id": "living_room_lights",
                "custom_name": "我的客厅灯",
                "is_favorite": true,
                "is_accessible": true,
                "min_familiarity_required": 25,
                "custom_permissions": {},
                "allowed_actions": ["turn_on", "turn_off", "set_brightness"],
                "user_preferences": {"default_brightness": 80},
                "quick_actions": ["turn_on", "turn_off"]
            }
        ],
        "overwrite_existing": false
    }
    """
    try:
        results = db_service.import_user_devices(
            user_id=user_id,
            devices_data=request.devices,
            overwrite_existing=request.overwrite_existing
        )
        
        return {
            "success": results["imported"] > 0 or results["updated"] > 0,
            "imported_count": results["imported"],
            "updated_count": results["updated"],
            "processed_devices": results["devices"],
            "errors": results["errors"],
            "message": f"成功导入 {results['imported']} 个设备配置，更新 {results['updated']} 个设备配置"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入用户设备配置失败: {str(e)}")

@app.post("/users/{user_id}/devices/export")
async def export_user_devices(user_id: str):
    """
    导出用户设备配置为JSON格式
    
    返回格式:
    {
        "user_id": "user_001",
        "devices": [
            {
                "device_id": "living_room_lights",
                "custom_name": "我的客厅灯",
                "is_favorite": true,
                "is_accessible": true,
                "min_familiarity_required": 25,
                "custom_permissions": {},
                "allowed_actions": ["turn_on", "turn_off", "set_brightness"],
                "user_preferences": {"default_brightness": 80},
                "quick_actions": ["turn_on", "turn_off"],
                "added_at": "2025-01-13T10:30:00Z",
                "last_used": "2025-01-13T16:00:00Z",
                "usage_count": 25
            }
        ],
        "export_info": {
            "total_count": 1,
            "export_time": "2025-01-13T16:05:00Z"
        }
    }
    """
    try:
        export_data = db_service.export_user_devices(user_id)
        return export_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出用户设备配置失败: {str(e)}")

# Chat endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process chat message"""
    start_time = time.time()
    
    try:
        # Process the request using the main planner
        response, conversation_id = await planner.process_request(
            user_input=request.message,
            user_id=request.user_id,
            conversation_id=request.conversation_id
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Get conversation context for response
        conversation_ctx = planner.active_conversations.get(conversation_id)
        familiarity_score = conversation_ctx.familiarity_score if conversation_ctx else 25
        message_count = conversation_ctx.message_count if conversation_ctx else 1
        
        # Save message to database
        db_service.save_message(
            conversation_id=conversation_id,
            user_input=request.message,
            assistant_response=response,
            tone_used=conversation_ctx.tone if conversation_ctx else "polite",
            processing_time_ms=processing_time
        )
        
        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            user_id=request.user_id,
            familiarity_score=familiarity_score,
            message_count=message_count,
            processing_time_ms=processing_time,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理消息失败: {str(e)}")

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    try:
        messages = db_service.get_conversation_history(conversation_id, limit=50)
        return {
            "conversation_id": conversation_id,
            "messages": [msg.to_dict() for msg in messages],
            "message_count": len(messages)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话历史失败: {str(e)}")

@app.delete("/conversations/{conversation_id}")
async def end_conversation(conversation_id: str):
    """End a conversation"""
    try:
        success = db_service.end_conversation(conversation_id)
        if success:
            # Also remove from memory cache
            if conversation_id in planner.active_conversations:
                del planner.active_conversations[conversation_id]
            return {"success": True, "message": f"对话 {conversation_id} 已结束"}
        else:
            raise HTTPException(status_code=404, detail="对话不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"结束对话失败: {str(e)}")

# Device control endpoints
@app.get("/devices")
async def list_devices(
    active_only: bool = Query(True),
    room: Optional[str] = Query(None),
    device_type: Optional[str] = Query(None)
):
    """List all available devices with optional filtering"""
    try:
        if room:
            devices = db_service.get_devices_by_room(room, active_only=active_only)
        elif device_type:
            devices = db_service.get_devices_by_type(device_type, active_only=active_only)
        else:
            devices = db_service.get_all_devices(active_only=active_only)
        
        return {
            "devices": [device.to_dict() for device in devices],
            "count": len(devices),
            "filters": {
                "active_only": active_only,
                "room": room,
                "device_type": device_type
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取设备列表失败: {str(e)}")

@app.post("/devices")
async def create_device(device_data: DeviceCreateRequest):
    """Create a new device"""
    try:
        device_dict = device_data.dict()
        
        # Set default values for supported_actions if not provided
        if not device_dict['supported_actions']:
            device_type = device_dict['device_type']
            if device_type == "lights":
                device_dict['supported_actions'] = ["turn_on", "turn_off", "set_brightness"]
            elif device_type == "tv":
                device_dict['supported_actions'] = ["turn_on", "turn_off", "set_volume", "set_channel"]
            elif device_type == "speaker":
                device_dict['supported_actions'] = ["turn_on", "turn_off", "set_volume"]
            else:
                device_dict['supported_actions'] = ["turn_on", "turn_off"]
        
        # Set default capabilities if not provided
        if not device_dict['capabilities']:
            device_type = device_dict['device_type']
            if device_type == "lights":
                device_dict['capabilities'] = {"brightness": {"min": 0, "max": 100}}
            elif device_type in ["tv", "speaker"]:
                device_dict['capabilities'] = {"volume": {"min": 0, "max": 100}}
        
        # Set initial state
        device_dict['current_state'] = {"status": "off"}
        
        device = db_service.create_device(device_dict)
        if device:
            return {
                "success": True,
                "device": device.to_dict(),
                "message": f"设备 {device_data.id} 创建成功"
            }
        else:
            raise HTTPException(status_code=409, detail=f"设备 {device_data.id} 已存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建设备失败: {str(e)}")

@app.get("/devices/{device_id}")
async def get_device_status(device_id: str):
    """Get device status"""
    try:
        device = db_service.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
        
        return device.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取设备状态失败: {str(e)}")

@app.put("/devices/{device_id}")
async def update_device(device_id: str, device_data: DeviceUpdateRequest):
    """Update device information"""
    try:
        updates = device_data.dict(exclude_unset=True)
        success = db_service.update_device(device_id, **updates)
        
        if success:
            device = db_service.get_device(device_id)
            return {
                "success": True,
                "device": device.to_dict(),
                "message": f"设备 {device_id} 信息已更新"
            }
        else:
            raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新设备失败: {str(e)}")

@app.delete("/devices/{device_id}")
async def delete_device(device_id: str, hard_delete: bool = Query(False)):
    """Delete device (soft delete by default)"""
    try:
        success = db_service.delete_device(device_id, soft_delete=not hard_delete)
        if success:
            delete_type = "永久删除" if hard_delete else "停用"
            return {"success": True, "message": f"设备 {device_id} 已{delete_type}"}
        else:
            raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除设备失败: {str(e)}")

@app.post("/devices/bulk")
async def bulk_create_devices(request: BulkDeviceImportRequest):
    """Bulk create devices"""
    try:
        devices_data = []
        for device in request.devices:
            device_dict = device.dict()
            
            # Set default values
            if not device_dict['supported_actions']:
                device_type = device_dict['device_type']
                if device_type == "lights":
                    device_dict['supported_actions'] = ["turn_on", "turn_off", "set_brightness"]
                elif device_type == "tv":
                    device_dict['supported_actions'] = ["turn_on", "turn_off", "set_volume", "set_channel"]
                elif device_type == "speaker":
                    device_dict['supported_actions'] = ["turn_on", "turn_off", "set_volume"]
                else:
                    device_dict['supported_actions'] = ["turn_on", "turn_off"]
            
            if not device_dict['capabilities']:
                device_type = device_dict['device_type']
                if device_type == "lights":
                    device_dict['capabilities'] = {"brightness": {"min": 0, "max": 100}}
                elif device_type in ["tv", "speaker"]:
                    device_dict['capabilities'] = {"volume": {"min": 0, "max": 100}}
            
            device_dict['current_state'] = {"status": "off"}
            devices_data.append(device_dict)
        
        results = db_service.bulk_create_devices(devices_data)
        
        return {
            "success": results["created"] > 0,
            "created_count": results["created"],
            "created_devices": results["devices"],
            "errors": results["errors"],
            "message": f"成功创建 {results['created']} 个设备"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量创建设备失败: {str(e)}")

@app.post("/devices/control", response_model=DeviceControlResponse)
async def control_device(request: DeviceControlRequest):
    """Control a device"""
    try:
        # Check user familiarity
        familiarity = db_service.get_user_familiarity(request.user_id)
        if familiarity < config.system.min_familiarity_for_hardware:
            return DeviceControlResponse(
                success=False,
                error=f"熟悉度不足 (当前: {familiarity}, 需要: {config.system.min_familiarity_for_hardware})",
                timestamp=datetime.utcnow()
            )
        
        # Execute device control
        result = planner.control_hardware(
            device=request.device_id,
            action=request.action,
            parameters=request.parameters
        )
        
        # Get updated device state
        device = db_service.get_device(request.device_id)
        device_state = device.current_state if device else None
        
        return DeviceControlResponse(
            success=result["success"],
            message=result.get("message"),
            error=result.get("error"),
            device_state=device_state,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"控制设备失败: {str(e)}")

# Memory management endpoints
@app.post("/users/{user_id}/memories")
async def save_user_memory(user_id: str, memory_data: UserMemoryRequest):
    """Save a user memory"""
    try:
        memory = db_service.save_user_memory(
            user_id=user_id,
            content=memory_data.content,
            memory_type=memory_data.memory_type,
            keywords=memory_data.keywords,
            importance_score=memory_data.importance_score
        )
        
        return {
            "success": True,
            "memory": memory.to_dict(),
            "message": "记忆已保存"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存记忆失败: {str(e)}")

@app.get("/users/{user_id}/memories")
async def search_user_memories(
    user_id: str,
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    memory_type: Optional[str] = None
):
    """Search user memories"""
    try:
        memories = db_service.search_user_memories(
            user_id=user_id,
            query=query,
            limit=limit,
            memory_type=memory_type
        )
        
        return {
            "memories": [memory.to_dict() for memory in memories],
            "count": len(memories),
            "query": query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索记忆失败: {str(e)}")

# Analytics endpoints
@app.get("/analytics/system")
async def get_system_analytics():
    """Get system-wide analytics"""
    try:
        stats = db_service.get_system_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统统计失败: {str(e)}")

@app.get("/analytics/users/{user_id}")
async def get_user_analytics(user_id: str):
    """Get user analytics"""
    try:
        stats = db_service.get_user_statistics(user_id)
        usage_stats = db_service.get_device_usage_stats(user_id=user_id, days=30)
        
        return {
            "user_statistics": stats,
            "device_usage": usage_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户统计失败: {str(e)}")

@app.get("/analytics/devices/{device_id}")
async def get_device_analytics(device_id: str, days: int = Query(7, ge=1, le=365)):
    """Get device usage analytics"""
    try:
        usage_stats = db_service.get_device_usage_stats(device_id=device_id, days=days)
        return {
            "device_id": device_id,
            "usage_statistics": usage_stats,
            "days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取设备统计失败: {str(e)}")

# Admin endpoints
@app.post("/admin/cleanup")
async def cleanup_expired_conversations():
    """Clean up expired conversations"""
    try:
        cleaned_count = db_service.cleanup_expired_conversations()
        planner.cleanup_expired_conversations()
        
        return {
            "success": True,
            "cleaned_conversations": cleaned_count,
            "message": f"清理了 {cleaned_count} 个过期对话"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")

@app.get("/admin/status")
async def get_admin_status():
    """Get admin status information"""
    try:
        system_stats = db_service.get_system_statistics()
        active_conversations = len(planner.active_conversations)
        
        return {
            "system_statistics": system_stats,
            "active_conversations_in_memory": active_conversations,
            "config": {
                "conversation_timeout_minutes": config.system.conversation_timeout_minutes,
                "max_active_conversations": config.system.max_active_conversations,
                "langfuse_enabled": config.langfuse.enabled,
                "vector_search_enabled": config.vector_search.enabled
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

# WebSocket support for real-time chat (optional)
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            conversation_id = data.get("conversation_id")
            
            if message:
                # Process message
                response, conv_id = await planner.process_request(
                    user_input=message,
                    user_id=user_id,
                    conversation_id=conversation_id
                )
                
                # Send response back
                await websocket.send_json({
                    "response": response,
                    "conversation_id": conv_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        print(f"WebSocket disconnected for user: {user_id}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "资源未找到", "status_code": 404}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "内部服务器错误", "status_code": 500}

# Run server
if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
