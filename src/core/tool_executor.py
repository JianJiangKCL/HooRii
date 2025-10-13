#!/usr/bin/env python3
"""
Tool Executor Component
Executes tools based on planner decisions
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

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
from .context_manager import SystemContext
from .intent_analyzer import IntentAnalyzer
from .device_controller import DeviceController
from ..services.agora_tts_service import AgoraTTSService
from ..services.database_service import DatabaseService


class ToolExecutor:
    """Executes tools and agents based on planner instructions"""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize tool services
        self.intent_analyzer = IntentAnalyzer(config)
        self.device_controller = DeviceController(config)
        self.agora_tts = AgoraTTSService(config)
        tts_selection = getattr(config, "tts", None)
        self.tts_provider = getattr(tts_selection, "provider", "openai")
        self.tts_default_voice = (
            getattr(tts_selection, "default_voice", None)
            or getattr(self.agora_tts, "default_voice", None)
        )
        self.tts_format = (
            getattr(tts_selection, "audio_format", "mp3")
            or getattr(self.agora_tts, "audio_format", "mp3")
        )
        self.database = DatabaseService(config)

    @observe(name="familiarity_check_tool")
    async def execute_familiarity_check(
        self,
        user_id: str,
        required_level: int = 40
    ) -> Dict[str, Any]:
        """执行熟悉度检查工具"""

        try:
            # Get current familiarity from context (simplified)
            # In real implementation, this would query the database
            current_level = 25  # Default level from config

            result = {
                "success": True,
                "current_familiarity": current_level,
                "required_familiarity": required_level,
                "check_passed": current_level >= required_level,
                "timestamp": datetime.now().isoformat()
            }

            self.logger.info(f"Familiarity check: {current_level}/{required_level} = {'PASS' if result['check_passed'] else 'FAIL'}")
            return result

        except Exception as e:
            self.logger.error(f"Familiarity check error: {e}")
            return {
                "success": False,
                "error": str(e),
                "current_familiarity": 0,
                "required_familiarity": required_level,
                "check_passed": False,
                "timestamp": datetime.now().isoformat()
            }

    @observe(name="device_control_tool")
    async def execute_device_control(
        self,
        device: str,
        action: str,
        parameters: Dict[str, Any] = None,
        context: SystemContext = None
    ) -> Dict[str, Any]:
        """执行设备控制工具"""

        try:
            self.logger.info(f"Executing device control: {device} -> {action}")

            # Create intent structure for device controller
            intent_analysis = {
                "involves_hardware": True,
                "device": device,
                "action": action,
                "parameters": parameters or {},
                "confidence": 0.9,
                "reasoning": "Tool executor initiated control"
            }

            # Use existing device controller
            result = await self.device_controller.process_device_intent(
                intent_analysis,
                context or SystemContext()
            )

            self.logger.info(f"Device control result: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Device control error: {e}")
            return {
                "success": False,
                "error": str(e),
                "device": device,
                "action": action,
                "timestamp": datetime.now().isoformat()
            }

    @observe(name="agora_tts_tool")
    async def execute_agora_tts(
        self,
        text: str,
        voice: str = None
    ) -> Dict[str, Any]:
        """执行声网TTS工具"""

        try:
            provider_label = (self.tts_provider or "tts").title()
            self.logger.info(f"Executing {provider_label} TTS for text: {text[:50]}...")

            voice_choice = voice or self.tts_default_voice
            resolved_voice = self.agora_tts._resolve_voice(voice_choice)  # noqa: SLF001 - using service helper

            # Call TTS service
            audio_base64 = await self.agora_tts.text_to_speech(
                text,
                voice=resolved_voice,
                audio_format=self.tts_format
            )

            if audio_base64:
                result = {
                    "success": True,
                    "audio_data": audio_base64,
                    "text": text,
                    "voice": resolved_voice,
                    "format": f"base64_{self.tts_format or 'mp3'}",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                result = {
                    "success": False,
                    "error": "TTS synthesis failed",
                    "text": text,
                    "voice": resolved_voice,
                    "timestamp": datetime.now().isoformat()
                }

            self.logger.info(f"{provider_label} TTS result: {'success' if result['success'] else 'failed'}")
            return result

        except Exception as e:
            self.logger.error(f"{(self.tts_provider or 'tts').title()} TTS error: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": text,
                "voice": voice,
                "timestamp": datetime.now().isoformat()
            }

    @observe(name="context_summary_tool")
    async def execute_context_summary(
        self,
        session_id: str,
        conversation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行上下文总结工具"""

        try:
            self.logger.info(f"Executing context summary for session: {session_id}")

            # Create conversation summary
            messages = conversation_data.get("messages", [])
            summary_data = {
                "session_id": session_id,
                "total_messages": len(messages),
                "start_time": conversation_data.get("start_time"),
                "end_time": datetime.now().isoformat(),
                "key_topics": conversation_data.get("topics", []),
                "device_actions": conversation_data.get("device_actions", []),
                "familiarity_changes": conversation_data.get("familiarity_changes", [])
            }

            # Store summary in database
            success = await self.database.store_conversation_summary(summary_data)

            result = {
                "success": success,
                "session_id": session_id,
                "summary_data": summary_data,
                "timestamp": datetime.now().isoformat()
            }

            self.logger.info(f"Context summary result: {'success' if success else 'failed'}")
            return result

        except Exception as e:
            self.logger.error(f"Context summary error: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }

    @observe(name="intent_analysis_tool")
    async def execute_intent_analysis(
        self,
        user_input: str,
        context: SystemContext
    ) -> Dict[str, Any]:
        """执行意图分析工具"""

        try:
            self.logger.info(f"Executing intent analysis for: {user_input}")

            # Use existing intent analyzer
            result = await self.intent_analyzer.analyze_intent(user_input, context)

            self.logger.info(f"Intent analysis result: confidence={result.get('confidence', 0)}")
            return {
                "success": True,
                "intent_result": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Intent analysis error: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_input": user_input,
                "timestamp": datetime.now().isoformat()
            }

    @observe(name="tool_execution")
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: SystemContext = None
    ) -> Dict[str, Any]:
        """通用工具执行接口"""

        self.logger.info(f"Executing tool: {tool_name} with params: {parameters}")

        try:
            if tool_name == "familiarity_check":
                return await self.execute_familiarity_check(
                    parameters.get("user_id", "default"),
                    parameters.get("required_level", 40)
                )

            elif tool_name == "device_control":
                return await self.execute_device_control(
                    parameters.get("device"),
                    parameters.get("action"),
                    parameters.get("parameters", {}),
                    context
                )

            elif tool_name == "agora_tts":
                return await self.execute_agora_tts(
                    parameters.get("text"),
                    parameters.get("voice")
                )

            elif tool_name == "context_summary":
                return await self.execute_context_summary(
                    parameters.get("session_id"),
                    parameters.get("conversation_data", {})
                )

            elif tool_name == "intent_analysis":
                return await self.execute_intent_analysis(
                    parameters.get("user_input"),
                    context or SystemContext()
                )

            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            self.logger.error(f"Tool execution error for {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "timestamp": datetime.now().isoformat()
            }

    @observe(name="execute_plan")
    async def execute_plan(
        self,
        plan: Dict[str, Any],
        context: SystemContext
    ) -> Dict[str, Any]:
        """执行完整的任务计划"""

        self.logger.info(f"Executing plan with {len(plan.get('plan', []))} steps")

        execution_results = []
        plan_steps = plan.get("plan", [])

        for step in plan_steps:
            step_num = step.get("step", 0)
            action = step.get("action")
            parameters = step.get("parameters", {})

            self.logger.info(f"Executing step {step_num}: {action}")

            # Execute tool
            result = await self.execute_tool(action, parameters, context)

            # Add step info to result
            result["step_number"] = step_num
            result["action"] = action
            result["reason"] = step.get("reason", "")

            execution_results.append(result)

            # If step failed and it's critical, stop execution
            if not result.get("success", False) and step.get("critical", False):
                self.logger.warning(f"Critical step {step_num} failed, stopping execution")
                break

        # Compile overall execution result
        overall_result = {
            "plan_execution_success": all(r.get("success", False) for r in execution_results),
            "total_steps": len(plan_steps),
            "executed_steps": len(execution_results),
            "step_results": execution_results,
            "execution_timestamp": datetime.now().isoformat(),
            "plan_metadata": plan.get("metadata", {})
        }

        success_count = sum(1 for r in execution_results if r.get("success", False))
        self.logger.info(f"Plan execution completed: {success_count}/{len(execution_results)} steps successful")

        return overall_result
