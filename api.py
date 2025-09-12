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
async def list_devices():
    """List all available devices"""
    try:
        devices = db_service.get_all_devices(active_only=True)
        return {
            "devices": [device.to_dict() for device in devices],
            "count": len(devices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取设备列表失败: {str(e)}")

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
