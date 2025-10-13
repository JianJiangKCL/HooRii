#!/usr/bin/env python3
"""
Task Planner Component
Plans and orchestrates complex tasks using available tools
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
from ..utils.llm_client import create_llm_client
from .context_manager import SystemContext


class TaskPlanner:
    """Plans and coordinates complex tasks using available tools"""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.llm_client = create_llm_client(config)

        # Available tools registry
        self.available_tools = {
            "familiarity_check": {
                "description": "检查用户熟悉度是否满足设备控制要求",
                "parameters": ["user_id", "required_level"],
                "returns": "familiarity_check_result"
            },
            "device_control": {
                "description": "控制智能家居设备",
                "parameters": ["device", "action", "parameters"],
                "returns": "device_control_result"
            },
            "agora_tts": {
                "description": "将文本转换为语音输出 (OpenAI GPT-4o-mini-tts)",
                "parameters": ["text", "voice"],
                "returns": "audio_data"
            },
            "context_summary": {
                "description": "总结对话上下文并存储到数据库",
                "parameters": ["session_id", "conversation_data"],
                "returns": "summary_result"
            },
            "intent_analysis": {
                "description": "分析用户意图和需求",
                "parameters": ["user_input", "context"],
                "returns": "intent_result"
            }
        }

    def _build_tools_prompt(self) -> str:
        """构建工具系统提示词"""
        tools_desc = []
        for tool_name, tool_info in self.available_tools.items():
            tools_desc.append(f"""
{tool_name}:
  描述: {tool_info['description']}
  参数: {', '.join(tool_info['parameters'])}
  返回: {tool_info['returns']}""")

        return f"""
可用工具列表:
{chr(10).join(tools_desc)}

使用格式:
{{
    "plan": [
        {{
            "step": 1,
            "action": "tool_name",
            "parameters": {{"param1": "value1", "param2": "value2"}},
            "reason": "执行原因"
        }}
    ],
    "reasoning": "整体规划思路"
}}
"""

    @observe(name="task_planning")
    async def make_plan(
        self,
        user_input: str,
        context: SystemContext,
        task_complexity: str = "simple"
    ) -> Dict[str, Any]:
        """制定任务执行计划"""

        self.logger.info(f"Starting task planning for: {user_input}")

        # 构建规划提示词
        tools_prompt = self._build_tools_prompt()
        familiarity = context.familiarity_score
        last_turn = context.get_conversation_context_for_llm(max_turns=2)

        planning_prompt = f"""
作为智能任务规划师，分析用户需求并制定执行计划。

用户输入: "{user_input}"
用户熟悉度: {familiarity}/100
上下文: {last_turn if last_turn else "无"}

{tools_prompt}

任务复杂度: {task_complexity}

规划要求:
1. 分析用户真实需求
2. 检查是否需要熟悉度验证（设备控制需要40+）
3. 确定需要调用的工具和顺序
4. 考虑凌波丽的角色特点
5. 如果需要语音输出，添加TTS步骤
6. 规划上下文管理（如对话结束需要总结）

输出JSON格式的执行计划。
"""

        try:
            system_prompt = "你是智能任务规划系统，负责分析用户需求并制定工具调用计划。"
            messages = [{"role": "user", "content": planning_prompt}]
            
            response_text = await self.llm_client.generate(
                system_prompt=system_prompt,
                messages=messages,
                max_tokens=500,
                temperature=0.2
            )

            # 解析JSON计划
            try:
                if '{' in response_text and '}' in response_text:
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    json_str = response_text[json_start:json_end]
                    plan = json.loads(json_str)
                else:
                    # 默认计划
                    plan = {
                        "plan": [
                            {
                                "step": 1,
                                "action": "intent_analysis",
                                "parameters": {"user_input": user_input},
                                "reason": "分析用户意图"
                            }
                        ],
                        "reasoning": "简单意图分析计划"
                    }
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse plan JSON: {e}")
                plan = {
                    "plan": [],
                    "reasoning": "计划解析失败，使用默认流程",
                    "error": str(e)
                }

            # 添加元数据
            plan["metadata"] = {
                "user_input": user_input,
                "familiarity_score": familiarity,
                "task_complexity": task_complexity,
                "planning_timestamp": datetime.now().isoformat(),
                "total_steps": len(plan.get("plan", []))
            }

            self.logger.info(f"Plan created with {len(plan.get('plan', []))} steps")
            return plan

        except Exception as e:
            self.logger.error(f"Task planning error: {e}")
            return {
                "plan": [],
                "reasoning": "规划失败，使用默认处理",
                "error": str(e),
                "metadata": {
                    "user_input": user_input,
                    "familiarity_score": familiarity,
                    "error_timestamp": datetime.now().isoformat()
                }
            }

    @observe(name="plan_validation")
    async def validate_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """验证计划的可行性"""

        validation_result = {
            "valid": True,
            "issues": [],
            "suggestions": []
        }

        try:
            plan_steps = plan.get("plan", [])

            for step in plan_steps:
                action = step.get("action")
                parameters = step.get("parameters", {})

                # 检查工具是否存在
                if action not in self.available_tools:
                    validation_result["valid"] = False
                    validation_result["issues"].append(f"Unknown tool: {action}")
                    continue

                # 检查必需参数
                required_params = self.available_tools[action]["parameters"]
                for param in required_params:
                    if param not in parameters:
                        validation_result["issues"].append(f"Missing parameter '{param}' for tool '{action}'")

            # 检查步骤顺序逻辑
            if len(plan_steps) > 1:
                # 熟悉度检查应该在设备控制之前
                device_step = None
                familiarity_step = None

                for i, step in enumerate(plan_steps):
                    if step.get("action") == "device_control":
                        device_step = i
                    elif step.get("action") == "familiarity_check":
                        familiarity_step = i

                if device_step is not None and familiarity_step is not None:
                    if familiarity_step > device_step:
                        validation_result["issues"].append("熟悉度检查应该在设备控制之前")

            self.logger.info(f"Plan validation: {'passed' if validation_result['valid'] else 'failed'}")
            return validation_result

        except Exception as e:
            self.logger.error(f"Plan validation error: {e}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "suggestions": []
            }

    async def get_plan_summary(self, plan: Dict[str, Any]) -> str:
        """获取计划摘要"""
        steps = plan.get("plan", [])
        if not steps:
            return "无执行步骤"

        summary_parts = []
        for step in steps:
            action = step.get("action", "unknown")
            reason = step.get("reason", "")
            summary_parts.append(f"{step.get('step', '?')}. {action} - {reason}")

        return "执行计划:\n" + "\n".join(summary_parts)
