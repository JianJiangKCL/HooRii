#!/usr/bin/env python3
"""
Device Controller Component
Handles device control and status queries using LLM-based understanding
"""
import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

# Try to import Langfuse components
try:
    from langfuse import observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from ..utils.config import Config
from ..utils.llm_client import create_llm_client
from ..services.database_service import DatabaseService
from .context_manager import SystemContext


class DeviceController:
    """Handles all device operations with LLM-based understanding"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db_service = DatabaseService(config)
        self.llm_client = create_llm_client(config)
        
        # Load system prompt
        self.system_prompt = self._load_prompt_file('prompts/device_controller.txt')

        # Load device specifications from config
        self.device_specs = self._load_device_specifications()
        
        # Load familiarity requirements from config
        self.familiarity_requirements = self._load_familiarity_requirements()
    
    def _load_prompt_file(self, filepath: str) -> str:
        """Load prompt from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Failed to load prompt file {filepath}: {e}")
            return "你是智能家居设备控制系统，处理设备操作请求。"

    def _load_device_specifications(self) -> Dict[str, Any]:
        """Load device specifications from config file"""
        try:
            with open('config/device_specifications.json', 'r', encoding='utf-8') as f:
                specs = json.load(f)
                self.logger.info(f"Loaded device specifications: {len(specs.get('devices', {}))} device types")
                return specs
        except Exception as e:
            self.logger.warning(f"Failed to load device specifications: {e}")
            return {"devices": {}, "command_output_format": {}}
    
    def _load_familiarity_requirements(self) -> Dict[str, Any]:
        """Load familiarity requirements from config file"""
        try:
            with open('config/familiarity_requirements.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load familiarity requirements: {e}")
            # Return default requirements if file not found
            return {
                "device_requirements": {
                    "air_conditioner": 60,
                    "speaker": 40,
                    "tv": 40,
                    "lights": 30,
                    "curtains": 30,
                    "dimmable_light": 30,
                    "curtain": 30,
                    "default": 50
                },
                "action_modifiers": {
                    "critical_actions": {
                        "set_temperature_high": 20,
                        "set_volume_high": 20
                    }
                },
                "tone_thresholds": {
                    "formal": 30,
                    "polite": 60,
                    "casual": 80,
                    "intimate": 100
                }
            }
    
    def _get_device_spec(self, device_type: str) -> Optional[Dict[str, Any]]:
        """Get device specification by device type"""
        devices = self.device_specs.get("devices", {})
        
        # Try direct match first
        if device_type in devices:
            return devices[device_type]
        
        # Try to match by device_type_id
        for device_name, spec in devices.items():
            if spec.get("device_type_id") == device_type:
                return spec
        
        return None
    
    @observe(as_type="generation", name="device_controller")
    async def process_device_intent(
        self,
        intent: Dict[str, Any],
        context: SystemContext
    ) -> Dict[str, Any]:
        """Process device intent using LLM with full context"""
        
        # Get all available devices for context
        all_devices = self._get_device_context()
        
        # Build comprehensive prompt with context
        device_prompt = self._build_device_prompt(
            intent=intent,
            context=context,
            devices=all_devices
        )
        
        try:
            # Use LLM to understand and process the request
            messages = [{"role": "user", "content": device_prompt}]
            
            response_text = await self.llm_client.generate(
                system_prompt=self.system_prompt,
                messages=messages,
                max_tokens=1000,
                temperature=0.3
            )
            
            result = self._parse_json_response(response_text)
            
            # Execute the action if it's a control command
            if result.get("action_type") == "control":
                execution_result = await self._execute_control(
                    result=result,
                    context=context
                )
                result["execution"] = execution_result
                
                # Update context with device state
                if execution_result.get("success"):
                    device_id = result.get("device_id")
                    new_state = execution_result.get("new_state", {})
                    context.update_device_state(device_id, new_state)
                    
            elif result.get("action_type") == "query":
                query_result = await self._execute_query(
                    result=result,
                    context=context
                )
                result["query_result"] = query_result
            
            # Log device control results (captured by @observe decorator)
            self.logger.info(f"Device control - Action: {result.get('action_type')}, Device: {result.get('device_id')}, Success: {result.get('execution', {}).get('success', False)}")
            
            self.logger.info(f"Device controller result: {json.dumps(result, ensure_ascii=False)}")
            return result
            
        except Exception as e:
            self.logger.error(f"Device controller error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "设备控制处理失败"
            }
    
    def _build_device_prompt(
        self,
        intent: Dict[str, Any],
        context: SystemContext,
        devices: Dict[str, Any]
    ) -> str:
        """Build comprehensive prompt for device control"""
        
        # Get conversation history
        max_turns = self.config.system.max_conversation_turns
        conv_history = context.get_conversation_context_for_llm(max_turns=max_turns)
        
        # Get current device states
        device_states = context.get_device_context_for_llm()
        
        prompt = f"""
分析并处理智能家居设备请求。

用户输入: "{context.user_input}"

意图分析结果:
{json.dumps(intent, ensure_ascii=False, indent=2)}

对话历史:
{conv_history if conv_history else "无历史对话"}

{device_states}

可用设备列表:
{json.dumps(devices, ensure_ascii=False, indent=2)}

上次设备操作:
{json.dumps(context.last_device_action, ensure_ascii=False) if context.last_device_action else "无"}

用户熟悉度: {context.familiarity_score}/100

任务说明:
1. 如果意图涉及设备控制(involves_hardware=true)，确定具体设备和操作
2. 如果有指代词(它、那个等)，从上下文推断具体设备
3. 如果是状态查询，返回相关设备的当前状态
4. 理解隐含意图，如"好热"可能意味着要开空调或调低温度
5. 考虑用户熟悉度，熟悉度低时操作需要更保守

返回JSON格式:
{{
    "action_type": "control/query/none",  // 操作类型
    "device_id": "具体设备ID",  // 目标设备
    "device_name": "设备名称",
    "command": "具体命令",  // 如turn_on, turn_off, set_brightness, set_hue, set_saturation, set_color, set_position, open_curtain, close_curtain等
    "parameters": {{  // 命令参数
        "brightness": number,  // 亮度 0-100
        "hue": number,  // 色值 0-360 (红0/橙30/黄60/绿120/青180/蓝240/紫270/品红300/紫红330)
        "saturation": number,  // 饱和度 0-100
        "temperature": number,  // 温度 16-30
        "volume": number,  // 音量 0-100
        "targetPosition": number,  // 窗帘位置 0-100 (0=关闭, 100=完全打开)
        "position": number  // 通用位置参数
    }},
    "query_devices": ["device_id1", "device_id2"],  // 查询的设备列表
    "reasoning": "决策理由",  // 解释为什么这样操作
    "confidence": 0.0-1.0,  // 置信度
    "message": "给用户的反馈消息",
    "requires_confirmation": boolean  // 是否需要用户确认
}}

只返回JSON，不要其他文字。
"""
        
        return prompt
    
    def _get_device_context(self) -> Dict[str, Any]:
        """Get all device information for context"""
        devices = self.db_service.get_all_devices(active_only=True)
        device_context = {}
        
        for device in devices:
            # Get device spec from configuration
            device_spec = self._get_device_spec(device.device_type)
            
            # Build capabilities based on spec
            capabilities = {}
            if device_spec:
                parameters = device_spec.get("parameters", {})
                capabilities = {
                    "can_dim": "brightness" in parameters,
                    "has_temperature": "temperature" in parameters,
                    "has_volume": "volume" in parameters,
                    "has_color": "hue" in parameters and "saturation" in parameters,
                    "has_position": "targetPosition" in parameters,
                    "supported_commands": device_spec.get("supported_commands", []),
                    "category": device_spec.get("category", "unknown")
                }
            else:
                # Fallback for devices without spec
                capabilities = {
                    "can_dim": device.device_type in ["light", "dimmable_light", "57D56F4D-3302-41F7-AB34-5365AA180E81"],
                    "has_temperature": device.device_type == "air_conditioner",
                    "has_volume": device.device_type == "speaker",
                    "has_color": device.device_type in ["dimmable_light", "57D56F4D-3302-41F7-AB34-5365AA180E81"],
                    "has_position": device.device_type in ["curtain", "2FB9EE1F-1C21-4D0B-9383-9B65F64DBF0E"]
                }
            
            device_context[device.id] = {
                "name": device.name,
                "type": device.device_type,
                "room": device.room,
                "current_state": device.current_state,
                "supported_actions": device.supported_actions,
                "capabilities": capabilities,
                "spec": device_spec  # Include full spec for reference
            }
        
        return device_context
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            if response_text.startswith('{') and response_text.endswith('}'):
                return json.loads(response_text)
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in response")
        except Exception as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            return {
                "action_type": "none",
                "error": "Failed to parse response",
                "raw_response": response_text[:500]
            }
    
    async def _execute_control(
        self,
        result: Dict[str, Any],
        context: SystemContext
    ) -> Dict[str, Any]:
        """Execute device control command"""
        device_id = result.get("device_id")
        command = result.get("command")
        parameters = result.get("parameters", {})
        
        if not device_id or not command:
            return {
                "success": False,
                "error": "Missing device_id or command"
            }
        
        # Get device from database
        db_device = self.db_service.get_device(device_id)
        if not db_device:
            return {
                "success": False,
                "error": f"Device {device_id} not found"
            }
        
        try:
            # Update device state
            new_state = db_device.current_state.copy()
            
            if command == "turn_on":
                new_state["isOn"] = True
                new_state["status"] = "on"
                # Apply default parameters if available
                if db_device.device_type in ["light", "57D56F4D-3302-41F7-AB34-5365AA180E81"]:
                    if "brightness" not in new_state:
                        new_state["brightness"] = 100
                    
            elif command == "turn_off":
                new_state["isOn"] = False
                new_state["status"] = "off"
                
            elif command == "set_brightness":
                brightness = parameters.get("brightness", 50)
                new_state["brightness"] = max(0, min(100, brightness))
                new_state["isOn"] = True
                new_state["status"] = "on"  # Turn on if setting brightness
                
            elif command == "set_hue":
                hue = parameters.get("hue", 0)
                new_state["hue"] = max(0, min(360, hue))
                new_state["isOn"] = True
                new_state["status"] = "on"  # Turn on if setting color
                
            elif command == "set_saturation":
                saturation = parameters.get("saturation", 50)
                new_state["saturation"] = max(0, min(100, saturation))
                new_state["isOn"] = True
                new_state["status"] = "on"  # Turn on if setting saturation
                
            elif command == "set_color":
                # Set both hue and saturation
                if "hue" in parameters:
                    new_state["hue"] = max(0, min(360, parameters["hue"]))
                if "saturation" in parameters:
                    new_state["saturation"] = max(0, min(100, parameters["saturation"]))
                new_state["isOn"] = True
                new_state["status"] = "on"
                
            elif command == "set_temperature":
                temperature = parameters.get("temperature", 24)
                new_state["temperature"] = max(16, min(30, temperature))
                new_state["status"] = "on"  # Turn on if setting temperature
                
            elif command == "set_volume":
                volume = parameters.get("volume", 50)
                new_state["volume"] = max(0, min(100, volume))
                new_state["status"] = "on"  # Turn on if setting volume
                
            elif command == "set_position" or command == "set_curtain_position":
                # For curtains - set targetPosition
                target_position = parameters.get("targetPosition", parameters.get("position", 0))
                new_state["targetPosition"] = max(0, min(100, target_position))
                new_state["currentPosition"] = new_state["targetPosition"]  # Simulate immediate movement
                new_state["isOn"] = new_state["targetPosition"] > 0
                new_state["status"] = "on" if new_state["targetPosition"] > 0 else "off"
                
            elif command == "open_curtain":
                new_state["targetPosition"] = 100
                new_state["currentPosition"] = 100
                new_state["isOn"] = True
                new_state["status"] = "on"
                
            elif command == "close_curtain":
                new_state["targetPosition"] = 0
                new_state["currentPosition"] = 0
                new_state["isOn"] = False
                new_state["status"] = "off"
                
            else:
                # Generic parameter update
                for key, value in parameters.items():
                    new_state[key] = value
            
            # Save to database
            self.db_service.update_device_state(device_id, new_state)
            
            # Log the interaction
            self.db_service.log_device_interaction(
                user_id=context.session_id,
                device_id=device_id,
                action=command,
                parameters=parameters,
                result={"new_state": new_state},
                success=True,
                conversation_id=context.session_id
            )
            
            # Build standard device control JSON output
            control_output = {
                "device_id": device_id,
                "device_name": db_device.name,
                "device_type": db_device.device_type,
                "command": command,
                "parameters": new_state,  # All current parameters
                "timestamp": datetime.now().isoformat(),
                "user_id": context.session_id if context else None,
                "familiarity_score": context.familiarity_score if context else None
            }
            
            return {
                "success": True,
                "device_id": device_id,
                "device_name": db_device.name,
                "command": command,
                "new_state": new_state,
                "control_output": control_output,  # Standard JSON format for external systems
                "message": f"{db_device.name} {self._get_action_description(command, parameters, new_state)}"
            }
            
        except Exception as e:
            self.logger.error(f"Execute control error: {e}")
            
            # Log failed interaction
            self.db_service.log_device_interaction(
                user_id=context.session_id,
                device_id=device_id,
                action=command,
                parameters=parameters,
                result={"error": str(e)},
                success=False,
                conversation_id=context.session_id,
                error_message=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "device_id": device_id
            }
    
    async def _execute_query(
        self,
        result: Dict[str, Any],
        context: SystemContext
    ) -> Dict[str, Any]:
        """Execute device status query"""
        query_devices = result.get("query_devices", [])
        
        if not query_devices:
            # Query all devices if none specified
            devices = self.db_service.get_all_devices(active_only=True)
            query_devices = [d.id for d in devices]
        
        status_info = {}
        for device_id in query_devices:
            db_device = self.db_service.get_device(device_id)
            if db_device:
                status_info[device_id] = {
                    "name": db_device.name,
                    "type": db_device.device_type,
                    "room": db_device.room,
                    "state": db_device.current_state,
                    "status_description": self._get_status_description(db_device)
                }
        
        return {
            "success": True,
            "devices": status_info,
            "summary": self._generate_status_summary(status_info)
        }
    
    def _get_action_description(
        self,
        command: str,
        parameters: Dict[str, Any],
        new_state: Dict[str, Any]
    ) -> str:
        """Generate human-readable action description"""
        if command == "turn_on":
            return "已开启"
        elif command == "turn_off":
            return "已关闭"
        elif command == "set_brightness":
            brightness = new_state.get("brightness", 0)
            return f"亮度已调整到 {brightness}%"
        elif command == "set_hue":
            hue = new_state.get("hue", 0)
            color_name = self._get_color_name_from_hue(hue)
            return f"色值已设置为 {hue}° ({color_name})"
        elif command == "set_saturation":
            saturation = new_state.get("saturation", 50)
            return f"饱和度已设置为 {saturation}%"
        elif command == "set_color":
            hue = new_state.get("hue", 0)
            saturation = new_state.get("saturation", 50)
            color_name = self._get_color_name_from_hue(hue)
            return f"颜色已设置为 {color_name} (色值: {hue}°, 饱和度: {saturation}%)"
        elif command == "set_temperature":
            temperature = new_state.get("temperature", 24)
            return f"温度已设置为 {temperature}°C"
        elif command == "set_volume":
            volume = new_state.get("volume", 50)
            return f"音量已设置为 {volume}%"
        elif command in ["set_position", "set_curtain_position"]:
            position = new_state.get("targetPosition", 0)
            return f"位置已设置为 {position}%"
        elif command == "open_curtain":
            return "窗帘已完全打开"
        elif command == "close_curtain":
            return "窗帘已完全关闭"
        else:
            return "操作已完成"
    
    def _get_color_name_from_hue(self, hue: int) -> str:
        """Convert hue value to color name in Chinese"""
        if 0 <= hue < 15 or 345 <= hue <= 360:
            return "红色"
        elif 15 <= hue < 45:
            return "橙色"
        elif 45 <= hue < 75:
            return "黄色"
        elif 75 <= hue < 105:
            return "黄绿"
        elif 105 <= hue < 135:
            return "绿色"
        elif 135 <= hue < 165:
            return "青绿"
        elif 165 <= hue < 195:
            return "青色"
        elif 195 <= hue < 225:
            return "靛蓝"
        elif 225 <= hue < 255:
            return "蓝色"
        elif 255 <= hue < 285:
            return "紫色"
        elif 285 <= hue < 315:
            return "品红"
        elif 315 <= hue < 345:
            return "紫红"
        else:
            return "未知颜色"
    
    def _get_status_description(self, device) -> str:
        """Generate human-readable status description"""
        state = device.current_state
        is_on = state.get("isOn", state.get("status") == "on")
        
        if not is_on:
            return f"{device.name}已关闭"
        else:
            desc = f"{device.name}已开启"
            
            # Light with color support (dimmable light)
            if device.device_type in ["light", "57D56F4D-3302-41F7-AB34-5365AA180E81"]:
                if "brightness" in state:
                    desc += f"，亮度{state['brightness']}%"
                if "hue" in state and "saturation" in state:
                    color_name = self._get_color_name_from_hue(state['hue'])
                    desc += f"，颜色{color_name}(色值{state['hue']}°，饱和度{state['saturation']}%)"
                elif "hue" in state:
                    color_name = self._get_color_name_from_hue(state['hue'])
                    desc += f"，颜色{color_name}(色值{state['hue']}°)"
                    
            # Curtain
            elif device.device_type in ["curtain", "2FB9EE1F-1C21-4D0B-9383-9B65F64DBF0E"]:
                if "currentPosition" in state:
                    desc = f"{device.name}位置{state['currentPosition']}%"
                    if state['currentPosition'] == 0:
                        desc = f"{device.name}已关闭"
                    elif state['currentPosition'] == 100:
                        desc = f"{device.name}已完全打开"
                elif "targetPosition" in state:
                    desc = f"{device.name}目标位置{state['targetPosition']}%"
                    
            # Air conditioner
            elif device.device_type == "air_conditioner" and "temperature" in state:
                desc += f"，温度{state['temperature']}°C"
                
            # Speaker
            elif device.device_type == "speaker" and "volume" in state:
                desc += f"，音量{state['volume']}%"
                
            return desc
    
    def _generate_status_summary(self, status_info: Dict[str, Any]) -> str:
        """Generate summary of device statuses"""
        if not status_info:
            return "没有找到任何设备"
        
        on_devices = []
        off_devices = []
        
        for device_id, info in status_info.items():
            if info["state"].get("status") == "on":
                on_devices.append(info["name"])
            else:
                off_devices.append(info["name"])
        
        summary_parts = []
        if on_devices:
            summary_parts.append(f"开启的设备: {', '.join(on_devices)}")
        if off_devices:
            summary_parts.append(f"关闭的设备: {', '.join(off_devices)}")
        
        return " | ".join(summary_parts) if summary_parts else "所有设备状态正常"
    
    @observe(as_type="generation", name="check_familiarity_requirement")
    async def check_familiarity_requirement(
        self,
        device_id: str,
        action: str,
        context: SystemContext
    ) -> Dict[str, Any]:
        """Check if user has sufficient familiarity for device control"""
        
        # Get device info
        db_device = self.db_service.get_device(device_id)
        if not db_device:
            return {
                "allowed": False,
                "reason": "device_not_found",
                "message": f"找不到设备 {device_id}"
            }
        
        # Use familiarity requirements from config
        device_reqs = self.familiarity_requirements.get("device_requirements", {})
        required_score = device_reqs.get(db_device.device_type, device_reqs.get("default", 50))

        # Critical actions need higher familiarity
        action_modifiers = self.familiarity_requirements.get("action_modifiers", {}).get("critical_actions", {})
        if action in ["set_temperature", "set_volume"] and "high" in str(context.current_intent.get("parameters", {})).lower():
            if action == "set_temperature":
                required_score += action_modifiers.get("set_temperature_high", 20)
            elif action == "set_volume":
                required_score += action_modifiers.get("set_volume_high", 20)
        
        if context.familiarity_score >= required_score:
            return {
                "allowed": True,
                "reason": "sufficient_familiarity",
                "message": None
            }
        else:
            return {
                "allowed": False,
                "reason": "insufficient_familiarity",
                "required_score": required_score,
                "current_score": context.familiarity_score,
                "message": f"需要更高的熟悉度才能控制{db_device.name}。当前熟悉度: {context.familiarity_score}，需要: {required_score}"
            }