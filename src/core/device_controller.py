#!/usr/bin/env python3
"""
Device Controller Component
Handles device control and status queries using LLM-based understanding
"""
import asyncio
import json
import logging
import re
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
    "command": "具体命令",  // 如turn_on, turn_off, set_brightness等
    "parameters": {{  // 命令参数
        "brightness": number,
        "temperature": number,
        "volume": number
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
            device_context[device.id] = {
                "name": device.name,
                "type": device.device_type,
                "room": device.room,
                "current_state": device.current_state,
                "supported_actions": device.supported_actions,
                "capabilities": {
                    "can_dim": device.device_type == "light",
                    "has_temperature": device.device_type == "air_conditioner",
                    "has_volume": device.device_type == "speaker"
                }
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
                new_state["status"] = "on"
                # Apply default parameters if available
                if db_device.device_type == "light" and "brightness" not in new_state:
                    new_state["brightness"] = 100
                    
            elif command == "turn_off":
                new_state["status"] = "off"
                
            elif command == "set_brightness":
                brightness = parameters.get("brightness", 50)
                new_state["brightness"] = max(0, min(100, brightness))
                new_state["status"] = "on"  # Turn on if setting brightness
                
            elif command == "set_temperature":
                temperature = parameters.get("temperature", 24)
                new_state["temperature"] = max(16, min(30, temperature))
                new_state["status"] = "on"  # Turn on if setting temperature
                
            elif command == "set_volume":
                volume = parameters.get("volume", 50)
                new_state["volume"] = max(0, min(100, volume))
                new_state["status"] = "on"  # Turn on if setting volume
                
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
            
            return {
                "success": True,
                "device_id": device_id,
                "device_name": db_device.name,
                "command": command,
                "new_state": new_state,
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
        elif command == "set_temperature":
            temperature = new_state.get("temperature", 24)
            return f"温度已设置为 {temperature}°C"
        elif command == "set_volume":
            volume = new_state.get("volume", 50)
            return f"音量已设置为 {volume}%"
        else:
            return "操作已完成"
    
    def _get_status_description(self, device) -> str:
        """Generate human-readable status description"""
        state = device.current_state
        status = state.get("status", "unknown")
        
        if status == "off":
            return f"{device.name}已关闭"
        elif status == "on":
            desc = f"{device.name}已开启"
            
            if device.device_type == "light" and "brightness" in state:
                desc += f"，亮度{state['brightness']}%"
            elif device.device_type == "air_conditioner" and "temperature" in state:
                desc += f"，温度{state['temperature']}°C"
            elif device.device_type == "speaker" and "volume" in state:
                desc += f"，音量{state['volume']}%"
                
            return desc
        else:
            return f"{device.name}状态未知"
    
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