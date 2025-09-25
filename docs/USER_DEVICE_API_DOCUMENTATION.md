# HooRii Smart Home AI Assistant - User Device Management API

## Overview

The HooRii system implements a user-device binding model where each user has their own personalized device list. This allows multiple users to share the same physical devices while maintaining individual access permissions, preferences, and configurations.

**Base URL**: `http://localhost:8000`

## Architecture

### Device vs User-Device Separation

1. **Global Devices** (`/devices`): Physical devices in the system with global configurations
2. **User Devices** (`/users/{user_id}/devices`): User-specific device configurations and access permissions

### Data Models

#### Global Device
```json
{
    "id": "living_room_lights",
    "name": "Living Room Lights",
    "device_type": "lights",
    "room": "living_room",
    "supported_actions": ["turn_on", "turn_off", "set_brightness"],
    "capabilities": {"brightness": {"min": 0, "max": 100}},
    "current_state": {"status": "off", "brightness": 0},
    "default_min_familiarity": 40,
    "is_active": true
}
```

#### User Device Configuration
```json
{
    "id": "uuid-string",
    "user_id": "user_001",
    "device_id": "living_room_lights",
    "custom_name": "My Living Room Lights",
    "is_favorite": true,
    "is_accessible": true,
    "min_familiarity_required": 25,
    "custom_permissions": {},
    "allowed_actions": ["turn_on", "turn_off"],
    "user_preferences": {"default_brightness": 80},
    "quick_actions": ["turn_on", "turn_off"],
    "added_at": "2025-01-13T10:30:00Z",
    "last_used": "2025-01-13T16:00:00Z",
    "usage_count": 25,
    "device": {
        // Full global device information
    }
}
```

## User Device Management APIs

### Get User's Device List

Retrieves all devices accessible to a specific user with their personalized configurations.

**Endpoint**: `GET /users/{user_id}/devices`

**Query Parameters**:
- `active_only` (boolean): Filter for accessible devices only (default: true)

**Response**:
```json
{
    "user_id": "user_001",
    "devices": [
        {
            "id": "uuid-string",
            "user_id": "user_001",
            "device_id": "living_room_lights",
            "custom_name": "My Living Room Lights",
            "is_favorite": true,
            "is_accessible": true,
            "min_familiarity_required": 25,
            "allowed_actions": ["turn_on", "turn_off", "set_brightness"],
            "user_preferences": {"default_brightness": 80},
            "quick_actions": ["turn_on", "turn_off"],
            "added_at": "2025-01-13T10:30:00Z",
            "last_used": "2025-01-13T16:00:00Z",
            "usage_count": 25,
            "device": {
                "id": "living_room_lights",
                "name": "Living Room Lights",
                "device_type": "lights",
                "room": "living_room",
                "supported_actions": ["turn_on", "turn_off", "set_brightness"],
                "capabilities": {"brightness": {"min": 0, "max": 100}},
                "current_state": {"status": "off", "brightness": 0}
            }
        }
    ],
    "count": 1,
    "active_only": true
}
```

### Add Device to User's List

Adds a global device to a user's personal device list with custom configuration.

**Endpoint**: `POST /users/{user_id}/devices`

**Request Body**:
```json
{
    "device_id": "living_room_lights",
    "custom_name": "My Living Room Lights",
    "is_favorite": true,
    "is_accessible": true,
    "min_familiarity_required": 25,
    "custom_permissions": {},
    "allowed_actions": ["turn_on", "turn_off", "set_brightness"],
    "user_preferences": {"default_brightness": 80},
    "quick_actions": ["turn_on", "turn_off"]
}
```

**Field Descriptions**:
- `device_id` (required): ID of the global device to add
- `custom_name` (optional): User's custom name for the device
- `is_favorite` (optional): Whether to mark as favorite (default: false)
- `is_accessible` (optional): Whether user can access this device (default: true)
- `min_familiarity_required` (optional): Override global familiarity requirement
- `custom_permissions` (optional): Custom permission settings
- `allowed_actions` (optional): Subset of device's supported actions (defaults to all)
- `user_preferences` (optional): User's preferred device settings
- `quick_actions` (optional): User's favorite quick actions

**Response**:
```json
{
    "success": true,
    "user_device": {
        // Full user device configuration
    },
    "message": "Device living_room_lights has been added to user user_001's device list"
}
```

### Get Specific User Device Configuration

Retrieves the configuration for a specific device in a user's list.

**Endpoint**: `GET /users/{user_id}/devices/{device_id}`

**Response**:
```json
{
    "id": "uuid-string",
    "user_id": "user_001",
    "device_id": "living_room_lights",
    "custom_name": "My Living Room Lights",
    "is_favorite": true,
    "is_accessible": true,
    "min_familiarity_required": 25,
    "allowed_actions": ["turn_on", "turn_off", "set_brightness"],
    "user_preferences": {"default_brightness": 80},
    "quick_actions": ["turn_on", "turn_off"],
    "added_at": "2025-01-13T10:30:00Z",
    "last_used": "2025-01-13T16:00:00Z",
    "usage_count": 25,
    "device": {
        // Full global device information
    }
}
```

### Update User Device Configuration

Updates the user's personalized configuration for a device.

**Endpoint**: `PUT /users/{user_id}/devices/{device_id}`

**Request Body**:
```json
{
    "custom_name": "Updated Device Name",
    "is_favorite": false,
    "is_accessible": true,
    "min_familiarity_required": 30,
    "custom_permissions": {"special_access": true},
    "allowed_actions": ["turn_on", "turn_off"],
    "user_preferences": {"default_brightness": 60},
    "quick_actions": ["turn_on"]
}
```

**Response**:
```json
{
    "success": true,
    "user_device": {
        // Updated user device configuration
    },
    "message": "Device configuration updated for user user_001's device living_room_lights"
}
```

### Remove Device from User's List

Removes a device from the user's personal device list.

**Endpoint**: `DELETE /users/{user_id}/devices/{device_id}`

**Response**:
```json
{
    "success": true,
    "message": "Device living_room_lights has been removed from user user_001's device list"
}
```

### Get User's Favorite Devices

Retrieves only the devices marked as favorites by the user.

**Endpoint**: `GET /users/{user_id}/devices/favorites`

**Response**:
```json
{
    "user_id": "user_001",
    "favorite_devices": [
        {
            // User device configurations for favorite devices only
        }
    ],
    "count": 1
}
```

## Bulk Operations

### Import User Device Configurations

Imports multiple device configurations for a user from JSON format.

**Endpoint**: `POST /users/{user_id}/devices/import`

**Request Body**:
```json
{
    "devices": [
        {
            "device_id": "living_room_lights",
            "custom_name": "My Living Room Lights",
            "is_favorite": true,
            "is_accessible": true,
            "min_familiarity_required": 25,
            "custom_permissions": {},
            "allowed_actions": ["turn_on", "turn_off", "set_brightness"],
            "user_preferences": {"default_brightness": 80},
            "quick_actions": ["turn_on", "turn_off"]
        },
        {
            "device_id": "bedroom_ac",
            "custom_name": "Bedroom Air Conditioner",
            "is_favorite": false,
            "is_accessible": true,
            "min_familiarity_required": 60,
            "allowed_actions": ["turn_on", "turn_off", "set_temperature"],
            "user_preferences": {"default_temperature": 24}
        }
    ],
    "overwrite_existing": false
}
```

**Response**:
```json
{
    "success": true,
    "imported_count": 2,
    "updated_count": 0,
    "processed_devices": ["living_room_lights", "bedroom_ac"],
    "errors": [],
    "message": "Successfully imported 2 device configurations, updated 0 device configurations"
}
```

### Export User Device Configurations

Exports all of a user's device configurations in JSON format.

**Endpoint**: `POST /users/{user_id}/devices/export`

**Response**:
```json
{
    "user_id": "user_001",
    "devices": [
        {
            "device_id": "living_room_lights",
            "custom_name": "My Living Room Lights",
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
```

## Usage Examples

### Example 1: Add a Device to User's List

```bash
curl -X POST "http://localhost:8000/users/john_doe/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "living_room_tv",
    "custom_name": "My TV",
    "is_favorite": true,
    "min_familiarity_required": 30,
    "allowed_actions": ["turn_on", "turn_off", "set_volume"],
    "user_preferences": {"default_volume": 25},
    "quick_actions": ["turn_on", "turn_off"]
  }'
```

### Example 2: Update Device Configuration

```bash
curl -X PUT "http://localhost:8000/users/john_doe/devices/living_room_tv" \
  -H "Content-Type: application/json" \
  -d '{
    "custom_name": "Johns TV",
    "is_favorite": false,
    "user_preferences": {"default_volume": 30}
  }'
```

### Example 3: Get User's Device List

```bash
curl "http://localhost:8000/users/john_doe/devices"
```

### Example 4: Export User's Device Configurations

```bash
curl -X POST "http://localhost:8000/users/john_doe/devices/export"
```

### Example 5: Import Device Configurations

```python
import requests
import json

# Prepare device configurations
device_configs = {
    "devices": [
        {
            "device_id": "kitchen_lights",
            "custom_name": "Kitchen Lights",
            "is_favorite": True,
            "min_familiarity_required": 20,
            "user_preferences": {"default_brightness": 90}
        },
        {
            "device_id": "smart_speaker",
            "custom_name": "My Speaker",
            "is_favorite": True,
            "allowed_actions": ["turn_on", "turn_off", "set_volume"],
            "quick_actions": ["turn_on", "set_volume"]
        }
    ],
    "overwrite_existing": False
}

# Import configurations
response = requests.post(
    "http://localhost:8000/users/john_doe/devices/import",
    headers={"Content-Type": "application/json"},
    json=device_configs
)

if response.status_code == 200:
    result = response.json()
    print(f"Imported {result['imported_count']} devices successfully")
    if result['errors']:
        print("Errors:", result['errors'])
else:
    print(f"Import failed: {response.text}")
```

## Device Access Control

### Familiarity-Based Access

Each user-device relationship can have a custom familiarity requirement that overrides the global device setting:

- **Global Device**: `default_min_familiarity: 60`
- **User Override**: `min_familiarity_required: 30`
- **Result**: User only needs 30 familiarity to access this device

### Action Restrictions

Users can have restricted access to device actions:

- **Global Device Actions**: `["turn_on", "turn_off", "set_temperature", "set_mode"]`
- **User Allowed Actions**: `["turn_on", "turn_off", "set_temperature"]`
- **Result**: User cannot use "set_mode" action

### Custom Permissions

Advanced permission systems can be implemented using the `custom_permissions` field:

```json
{
    "custom_permissions": {
        "schedule_access": true,
        "remote_access": false,
        "admin_functions": false,
        "energy_monitoring": true
    }
}
```

## Best Practices

### 1. Device Management Workflow

1. **Admin creates global devices** using `/devices` endpoints
2. **Users add devices to their list** using `/users/{user_id}/devices`
3. **Users customize their device settings** as needed
4. **System respects user-specific configurations** during device operations

### 2. Data Migration

When migrating user data:

1. **Export configurations** using the export endpoint
2. **Modify data** as needed for the new system
3. **Import configurations** using the import endpoint with `overwrite_existing: true`

### 3. Multi-User Scenarios

- **Family Setup**: Each family member has their own device list with different access levels
- **Guest Access**: Temporary users get limited device access with high familiarity requirements
- **Admin Users**: System administrators have access to all devices with low familiarity requirements

### 4. Error Handling

Always check for common error scenarios:

- **404 Not Found**: Device doesn't exist in global devices or user's device list
- **409 Conflict**: Device already exists in user's device list
- **403 Forbidden**: User doesn't have sufficient familiarity to access device
- **400 Bad Request**: Invalid device configuration or missing required fields

## Integration with Chat System

When users interact with devices through the chat interface, the system:

1. **Checks user's device list** to verify access
2. **Applies user-specific settings** (custom names, preferences)
3. **Respects access restrictions** (allowed actions, familiarity requirements)
4. **Updates usage statistics** (last_used, usage_count)

This ensures that each user has a personalized experience while maintaining security and access control.
