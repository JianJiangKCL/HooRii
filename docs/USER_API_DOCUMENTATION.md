# HooRii Smart Home AI Assistant - User API Documentation

## Overview

The HooRii Smart Home AI Assistant provides RESTful APIs for comprehensive user and device management. This documentation covers all endpoints related to user operations, device management, and data import/export functionality.

**Base URL**: `http://localhost:8000`

**Content-Type**: `application/json`

## Authentication

Currently, the API uses a simple token-based authentication system. For production use, proper JWT authentication should be implemented.

## User Management APIs

### Create User

Creates a new user in the system.

**Endpoint**: `POST /users`

**Request Body**:
```json
{
    "username": "string",           // Required: User's display name
    "email": "string",              // Optional: User's email address
    "familiarity_score": "integer"  // Optional: Initial familiarity score (0-100), default: 25
}
```

**Response**:
```json
{
    "success": true,
    "user": {
        "id": "string",
        "username": "string",
        "email": "string",
        "familiarity_score": 25,
        "preferred_tone": "polite",
        "preferences": {},
        "created_at": "2025-01-13T10:30:00Z",
        "last_seen": "2025-01-13T10:30:00Z",
        "is_active": true
    },
    "message": "User created successfully"
}
```

### Get User Information

Retrieves detailed information about a specific user.

**Endpoint**: `GET /users/{user_id}`

**Parameters**:
- `user_id` (path): User identifier

**Response**:
```json
{
    "user": {
        "id": "string",
        "username": "string",
        "email": "string",
        "familiarity_score": 75,
        "preferred_tone": "casual",
        "preferences": {},
        "created_at": "2025-01-13T10:30:00Z",
        "last_seen": "2025-01-13T16:00:00Z",
        "is_active": true
    },
    "statistics": {
        "user_id": "string",
        "familiarity_score": 75,
        "conversation_count": 15,
        "message_count": 150,
        "device_interaction_count": 45,
        "memory_count": 8,
        "member_since": "2025-01-13T10:30:00Z",
        "last_seen": "2025-01-13T16:00:00Z"
    }
}
```

### Update User Information

Updates user profile information.

**Endpoint**: `PUT /users/{user_id}`

**Request Body**:
```json
{
    "username": "string",           // Optional: New username
    "email": "string",              // Optional: New email
    "familiarity_score": "integer", // Optional: New familiarity score (0-100)
    "preferred_tone": "string",     // Optional: formal|polite|casual|intimate
    "preferences": {},              // Optional: User preferences object
    "is_active": "boolean"          // Optional: User active status
}
```

**Response**:
```json
{
    "success": true,
    "user": {
        // Updated user object
    },
    "message": "User information updated successfully"
}
```

### Update User Familiarity Score

Updates only the familiarity score for a user.

**Endpoint**: `PUT /users/{user_id}/familiarity`

**Request Body**:
```json
75  // Integer between 0 and 100
```

**Response**:
```json
{
    "success": true,
    "message": "User familiarity score updated to 75"
}
```

### List All Users

Retrieves a paginated list of users.

**Endpoint**: `GET /users`

**Query Parameters**:
- `active_only` (boolean): Filter for active users only (default: true)
- `limit` (integer): Maximum number of results (1-1000, default: 100)
- `offset` (integer): Number of results to skip (default: 0)

**Response**:
```json
{
    "users": [
        {
            // User objects
        }
    ],
    "count": 25,
    "limit": 100,
    "offset": 0
}
```

### Delete User

Removes a user from the system.

**Endpoint**: `DELETE /users/{user_id}`

**Query Parameters**:
- `hard_delete` (boolean): Permanently delete user (default: false for soft delete)

**Response**:
```json
{
    "success": true,
    "message": "User has been deactivated"
}
```

### Bulk Create Users

Creates multiple users in a single operation.

**Endpoint**: `POST /users/bulk`

**Request Body**:
```json
{
    "users": [
        {
            "username": "string",
            "email": "string",
            "familiarity_score": "integer"
        }
    ]
}
```

**Response**:
```json
{
    "success": true,
    "created_count": 5,
    "created_users": ["user1", "user2", "user3", "user4", "user5"],
    "errors": [],
    "message": "Successfully created 5 users"
}
```

## Device Management APIs

### List Devices

Retrieves a list of available devices with optional filtering.

**Endpoint**: `GET /devices`

**Query Parameters**:
- `active_only` (boolean): Filter for active devices only (default: true)
- `room` (string): Filter by room name
- `device_type` (string): Filter by device type

**Response**:
```json
{
    "devices": [
        {
            "id": "living_room_lights",
            "name": "Living Room Lights",
            "device_type": "lights",
            "room": "living_room",
            "supported_actions": ["turn_on", "turn_off", "set_brightness"],
            "capabilities": {
                "brightness": {"min": 0, "max": 100}
            },
            "current_state": {
                "status": "off",
                "brightness": 0
            },
            "min_familiarity_required": 30,
            "requires_auth": false,
            "is_active": true,
            "last_updated": "2025-01-13T16:00:00Z"
        }
    ],
    "count": 10,
    "filters": {
        "active_only": true,
        "room": null,
        "device_type": null
    }
}
```

### Create Device

Creates a new device in the system.

**Endpoint**: `POST /devices`

**Request Body**:
```json
{
    "id": "string",                     // Required: Unique device identifier
    "name": "string",                   // Required: Device display name
    "device_type": "string",            // Required: Device type (lights|tv|speaker|air_conditioner|curtains|other)
    "room": "string",                   // Optional: Room location
    "supported_actions": ["string"],    // Optional: Will auto-set based on device_type
    "capabilities": {},                 // Optional: Will auto-set based on device_type
    "min_familiarity_required": 40,    // Optional: Minimum familiarity score required (0-100)
    "requires_auth": false              // Optional: Whether device requires authentication
}
```

**Response**:
```json
{
    "success": true,
    "device": {
        // Created device object
    },
    "message": "Device created successfully"
}
```

### Get Device Status

Retrieves detailed information about a specific device.

**Endpoint**: `GET /devices/{device_id}`

**Response**:
```json
{
    "id": "living_room_lights",
    "name": "Living Room Lights",
    "device_type": "lights",
    "room": "living_room",
    "supported_actions": ["turn_on", "turn_off", "set_brightness"],
    "capabilities": {
        "brightness": {"min": 0, "max": 100}
    },
    "current_state": {
        "status": "on",
        "brightness": 75
    },
    "min_familiarity_required": 30,
    "requires_auth": false,
    "is_active": true,
    "last_updated": "2025-01-13T16:00:00Z"
}
```

### Update Device

Updates device information.

**Endpoint**: `PUT /devices/{device_id}`

**Request Body**:
```json
{
    "name": "string",                   // Optional: New device name
    "device_type": "string",            // Optional: New device type
    "room": "string",                   // Optional: New room location
    "supported_actions": ["string"],    // Optional: Supported actions list
    "capabilities": {},                 // Optional: Device capabilities
    "current_state": {},                // Optional: Current device state
    "min_familiarity_required": 40,    // Optional: Required familiarity score
    "requires_auth": false,             // Optional: Authentication requirement
    "is_active": true                   // Optional: Device active status
}
```

### Delete Device

Removes a device from the system.

**Endpoint**: `DELETE /devices/{device_id}`

**Query Parameters**:
- `hard_delete` (boolean): Permanently delete device (default: false for soft delete)

### Control Device

Executes a control command on a device.

**Endpoint**: `POST /devices/control`

**Request Body**:
```json
{
    "device_id": "string",      // Required: Target device ID
    "action": "string",         // Required: Action to perform
    "parameters": {},           // Optional: Action parameters
    "user_id": "string"         // Required: User performing the action
}
```

**Response**:
```json
{
    "success": true,
    "message": "Device controlled successfully",
    "error": null,
    "device_state": {
        "status": "on",
        "brightness": 80
    },
    "timestamp": "2025-01-13T16:05:00Z"
}
```

### Bulk Create Devices

Creates multiple devices in a single operation.

**Endpoint**: `POST /devices/bulk`

**Request Body**:
```json
{
    "devices": [
        {
            "id": "string",
            "name": "string",
            "device_type": "string",
            "room": "string",
            "min_familiarity_required": 40
        }
    ]
}
```

## JSON Import/Export APIs

### Import Users from JSON

Imports user data from JSON format.

**Endpoint**: `POST /users/import/json`

**Request Body**:
```json
{
    "users": [
        {
            "id": "user_001",
            "username": "John Doe",
            "email": "john@example.com",
            "familiarity_score": 75,
            "preferred_tone": "casual",
            "preferences": {
                "theme": "dark",
                "language": "en"
            },
            "is_active": true
        }
    ],
    "overwrite_existing": false
}
```

**Response**:
```json
{
    "success": true,
    "imported_count": 1,
    "updated_count": 0,
    "processed_users": ["user_001"],
    "errors": [],
    "message": "Successfully imported 1 users, updated 0 users"
}
```

### Export Users to JSON

Exports user data in JSON format.

**Endpoint**: `POST /users/export/json`

**Request Body** (Optional):
```json
{
    "include_inactive": false,
    "user_ids": ["user_001", "user_002"]
}
```

**Response**:
```json
{
    "users": [
        {
            "id": "user_001",
            "username": "John Doe",
            "email": "john@example.com",
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
        "include_inactive": false,
        "filtered_user_ids": ["user_001", "user_002"]
    }
}
```

### Import Devices from JSON

Imports device data from JSON format.

**Endpoint**: `POST /devices/import/json`

**Request Body**:
```json
{
    "devices": [
        {
            "id": "living_room_light_001",
            "name": "Living Room Main Light",
            "device_type": "lights",
            "room": "living_room",
            "supported_actions": ["turn_on", "turn_off", "set_brightness"],
            "capabilities": {
                "brightness": {"min": 0, "max": 100}
            },
            "current_state": {
                "status": "off",
                "brightness": 0
            },
            "min_familiarity_required": 30,
            "requires_auth": false,
            "is_active": true
        }
    ],
    "overwrite_existing": false
}
```

### Export Devices to JSON

Exports device data in JSON format.

**Endpoint**: `POST /devices/export/json`

**Request Body** (Optional):
```json
{
    "include_inactive": false,
    "device_ids": ["living_room_light_001", "bedroom_ac"]
}
```

## Chat and Conversation APIs

### Send Chat Message

Processes a chat message and returns AI response.

**Endpoint**: `POST /chat`

**Request Body**:
```json
{
    "message": "string",            // Required: User's message
    "user_id": "string",            // Required: User identifier
    "conversation_id": "string"     // Optional: Existing conversation ID
}
```

**Response**:
```json
{
    "response": "AI assistant response text",
    "conversation_id": "conv_12345",
    "user_id": "user_001",
    "familiarity_score": 75,
    "message_count": 5,
    "processing_time_ms": 1250.5,
    "timestamp": "2025-01-13T16:05:00Z"
}
```

### Get Conversation History

Retrieves message history for a conversation.

**Endpoint**: `GET /conversations/{conversation_id}`

**Response**:
```json
{
    "conversation_id": "conv_12345",
    "messages": [
        {
            "id": "msg_001",
            "user_input": "Turn on the lights",
            "assistant_response": "I've turned on the living room lights for you.",
            "timestamp": "2025-01-13T16:00:00Z"
        }
    ],
    "message_count": 10
}
```

### End Conversation

Terminates an active conversation.

**Endpoint**: `DELETE /conversations/{conversation_id}`

## Memory Management APIs

### Save User Memory

Stores a memory for a user.

**Endpoint**: `POST /users/{user_id}/memories`

**Request Body**:
```json
{
    "content": "string",            // Required: Memory content
    "memory_type": "string",        // Optional: Memory type (default: "general")
    "keywords": ["string"],         // Optional: Search keywords
    "importance_score": 1.0         // Optional: Importance score (0.0-1.0)
}
```

### Search User Memories

Searches through a user's stored memories.

**Endpoint**: `GET /users/{user_id}/memories`

**Query Parameters**:
- `query` (string): Search query
- `limit` (integer): Maximum results (1-50, default: 10)
- `memory_type` (string): Filter by memory type

## Analytics APIs

### Get System Analytics

Retrieves system-wide statistics.

**Endpoint**: `GET /analytics/system`

**Response**:
```json
{
    "active_users": 25,
    "total_conversations": 150,
    "active_conversations": 5,
    "total_messages": 1250,
    "active_devices": 15,
    "generated_at": "2025-01-13T16:05:00Z"
}
```

### Get User Analytics

Retrieves analytics for a specific user.

**Endpoint**: `GET /analytics/users/{user_id}`

### Get Device Analytics

Retrieves usage analytics for a device.

**Endpoint**: `GET /analytics/devices/{device_id}`

**Query Parameters**:
- `days` (integer): Number of days to analyze (1-365, default: 7)

## Administrative APIs

### Cleanup Expired Conversations

Removes expired conversation sessions.

**Endpoint**: `POST /admin/cleanup`

### Get Admin Status

Retrieves system status information.

**Endpoint**: `GET /admin/status`

## WebSocket API

### Real-time Chat

Establishes a WebSocket connection for real-time chat.

**Endpoint**: `WS /ws/{user_id}`

**Message Format**:
```json
{
    "message": "User message text",
    "conversation_id": "optional_conv_id"
}
```

## Error Handling

All API endpoints return appropriate HTTP status codes:

- `200 OK`: Successful operation
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

Error Response Format:
```json
{
    "detail": "Error description",
    "status_code": 400
}
```

## Data Types and Validation

### User Preferred Tone
- `formal`: Formal communication style
- `polite`: Polite communication style (default)
- `casual`: Casual communication style
- `intimate`: Intimate communication style

### Device Types
- `lights`: Lighting devices
- `tv`: Television devices
- `speaker`: Audio devices
- `air_conditioner`: Climate control devices
- `curtains`: Window covering devices
- `other`: Other device types

### Familiarity Score
Integer value between 0 and 100 representing user familiarity with the system.

## Rate Limiting

API endpoints are subject to rate limiting to ensure system stability. Current limits:
- Standard endpoints: 100 requests per minute per user
- Chat endpoints: 30 requests per minute per user
- Bulk operations: 10 requests per minute per user

## Version Information

Current API Version: v1.0.0
Documentation Last Updated: January 13, 2025
