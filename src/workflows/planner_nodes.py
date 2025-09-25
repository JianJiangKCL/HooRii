#!/usr/bin/env python3
"""
Planner-based workflow nodes for LangGraph
"""
from typing import Dict, Any
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


class PlannerNodes:
    """Collection of planner-based workflow nodes"""

    @observe(name="make_plan_node")
    async def _make_plan_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Planner node - creates execution plan"""
        try:
            self.logger.info("Starting task planning")

            # Load context
            context = await self._load_context(state)

            # Create execution plan
            plan = await self.task_planner.make_plan(
                state["user_input"],
                context,
                task_complexity="auto"
            )

            return {
                **state,
                "context": context.to_dict() if context else {},
                "execution_plan": plan,
                "metadata": {
                    "planning_timestamp": datetime.now().isoformat(),
                    "planner_mode": True
                }
            }

        except Exception as e:
            self.logger.error(f"Task planning failed: {e}")
            return {**state, "error": f"Task planning failed: {str(e)}"}

    @observe(name="execute_plan_node")
    async def _execute_plan_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plan node - runs planned tools"""
        try:
            self.logger.info("Executing task plan")

            execution_plan = state.get("execution_plan", {})
            context = await self._load_context(state)

            # Execute the plan using tool executor
            execution_result = await self.tool_executor.execute_plan(
                execution_plan,
                context
            )

            # Extract results for character response
            intent_analysis = None
            character_response = None
            device_actions = []

            # Parse execution results
            for step_result in execution_result.get("step_results", []):
                action = step_result.get("action")

                if action == "intent_analysis" and step_result.get("success"):
                    intent_analysis = step_result.get("intent_result", {})
                elif action == "device_control" and step_result.get("success"):
                    device_actions.append(step_result)
                elif action == "fast_processing" and step_result.get("success"):
                    # Fast processing includes both intent and response
                    result_data = step_result.get("result", {})
                    intent_analysis = result_data.get("intent_analysis")
                    character_response = result_data.get("response")

            # If no character response yet, generate one based on results
            if not character_response and intent_analysis:
                response_data = {
                    "intent_analysis": intent_analysis,
                    "device_actions": device_actions,
                    "execution_result": execution_result
                }
                character_response = await self.character_system.generate_response(
                    context,
                    response_data
                )

            return {
                **state,
                "intent_analysis": intent_analysis,
                "device_actions": device_actions,
                "character_response": character_response or "......",
                "execution_result": execution_result,
                "metadata": {
                    **state.get("metadata", {}),
                    "execution_timestamp": datetime.now().isoformat(),
                    "tools_executed": len(execution_result.get("step_results", []))
                }
            }

        except Exception as e:
            self.logger.error(f"Plan execution failed: {e}")
            return {**state, "error": f"Plan execution failed: {str(e)}"}

    @observe(name="generate_audio_node")
    async def _generate_audio_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Audio generation node - converts text to speech"""
        try:
            self.logger.info("Generating audio output")

            character_response = state.get("character_response", "")
            if not character_response:
                return {**state, "audio_data": None}

            # Generate audio using Agora TTS
            audio_result = await self.tool_executor.execute_agora_tts(
                character_response,
                voice="zh-CN-XiaoxiaoNeural"
            )

            return {
                **state,
                "audio_data": audio_result.get("audio_data") if audio_result.get("success") else None,
                "audio_generation_result": audio_result,
                "metadata": {
                    **state.get("metadata", {}),
                    "audio_generation_timestamp": datetime.now().isoformat(),
                    "audio_enabled": bool(audio_result.get("success"))
                }
            }

        except Exception as e:
            self.logger.error(f"Audio generation failed: {e}")
            return {**state, "error": f"Audio generation failed: {str(e)}"}

    def _should_execute_plan(self, state: Dict[str, Any]) -> str:
        """Conditional edge for plan execution"""
        if state.get("error"):
            return "error"

        execution_plan = state.get("execution_plan", {})
        plan_steps = execution_plan.get("plan", [])

        if plan_steps:
            self.logger.info(f"Plan has {len(plan_steps)} steps, executing")
            return "execute"
        else:
            self.logger.warning("No execution plan found")
            return "error"

    def _should_generate_audio(self, state: Dict[str, Any]) -> str:
        """Conditional edge for audio generation"""
        if state.get("error"):
            return "error"

        # Check if audio generation is needed and enabled
        if self.agora_tts.enabled and state.get("character_response"):
            return "generate_audio"
        else:
            return "skip_audio"