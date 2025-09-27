#!/usr/bin/env python3
"""
LangGraph-based workflow for Home AI System
Orchestrates intent analysis, device control, and character responses using LangGraph state management
"""
import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from datetime import datetime
import logging

try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
    print("✅ LangGraph available")
except ImportError:
    print("⚠️ Warning: LangGraph not available")
    LANGGRAPH_AVAILABLE = False

# Try to import Langfuse for observability
try:
    from langfuse import Langfuse, observe
    LANGFUSE_AVAILABLE = True
    print("✅ Langfuse SDK available for LangGraph")
except ImportError:
    print("⚠️ Warning: Langfuse not available")
    LANGFUSE_AVAILABLE = False
    Langfuse = None
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from ..utils.config import Config, load_config
from ..services.database_service import DatabaseService
from ..core.context_manager import ContextManager, SystemContext
from ..core.intent_analyzer import IntentAnalyzer
from ..core.device_controller import DeviceController
from ..core.character_system import CharacterSystem
from ..utils.task_planner import TaskPlanner
from ..core.tool_executor import ToolExecutor
from ..services.langfuse_session_manager import LangfuseSessionManager
from ..services.agora_tts_service import AgoraTTSService
from ..services.conversation_summary_service import ConversationSummaryService
from .planner_nodes import PlannerNodes

# State definition for LangGraph
class AISystemState(TypedDict):
    user_input: str
    user_id: Optional[str]
    session_id: Optional[str]
    context: Optional[Dict]
    intent_analysis: Optional[Dict]
    device_actions: Optional[List[Dict]]
    character_response: Optional[str]
    audio_data: Optional[str]
    audio_generation_result: Optional[Dict]
    final_response: Optional[str]
    error: Optional[str]
    metadata: Optional[Dict]

class LangGraphHomeAISystem:
    """LangGraph-based Home AI System orchestrator"""

    def __init__(self, config: Config = None):
        self.config = config or load_config()
        self.logger = logging.getLogger(__name__)

        # Initialize Langfuse if available
        self.langfuse_enabled = self.config.langfuse.enabled and LANGFUSE_AVAILABLE
        self.langfuse_client = None
        self.current_trace = None

        if self.langfuse_enabled:
            try:
                # Initialize Langfuse client
                self.langfuse_client = Langfuse(
                    public_key=self.config.langfuse.public_key,
                    secret_key=self.config.langfuse.secret_key,
                    host=self.config.langfuse.host
                )
                self.logger.info("Langfuse integration enabled for LangGraph")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Langfuse: {e}")
                self.langfuse_enabled = False

        # Initialize services
        self.db_service = DatabaseService(self.config)
        self.context_manager = ContextManager()
        self.intent_analyzer = IntentAnalyzer(self.config)
        self.device_controller = DeviceController(self.config)
        self.character_system = CharacterSystem(self.config)
        self.task_planner = TaskPlanner(self.config)
        self.tool_executor = ToolExecutor(self.config)
        self.agora_tts = AgoraTTSService(self.config)
        self.conversation_summary = ConversationSummaryService(self.config)
        self.session_manager = LangfuseSessionManager(self.config)
        # Use unified task planner approach
        self.use_unified_mode = True

        # Initialize LangGraph workflow
        if LANGGRAPH_AVAILABLE:
            self.memory = MemorySaver()
            self.workflow = self._create_workflow()
        else:
            self.workflow = None
            self.memory = None

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(AISystemState)

        if self.use_unified_mode:
            # Unified mode: Use task planner for all processing
            workflow.add_node("task_plan", self._task_plan_node)
            workflow.add_node("execute_device_actions", self._execute_device_actions_node)
            workflow.add_node("generate_audio", self._generate_audio_node)
            workflow.add_node("finalize_response", self._finalize_response_node)
            workflow.add_node("handle_error", self._handle_error_node)

            # Define edges for unified mode
            workflow.add_edge(START, "task_plan")
            workflow.add_conditional_edges(
                "task_plan",
                self._should_execute_devices,
                {
                    "execute": "execute_device_actions",
                    "skip": "generate_audio",
                    "error": "handle_error"
                }
            )
            workflow.add_edge("execute_device_actions", "generate_audio")
            workflow.add_edge("generate_audio", "finalize_response")
            workflow.add_edge("finalize_response", END)
            workflow.add_edge("handle_error", END)
        else:
            # Legacy mode (kept for compatibility)
            workflow.add_node("task_plan", self._task_plan_node)
            workflow.add_node("execute_device_actions", self._execute_device_actions_node)
            workflow.add_node("generate_audio", self._generate_audio_node)
            workflow.add_node("finalize_response", self._finalize_response_node)
            workflow.add_node("handle_error", self._handle_error_node)

            # Define edges for legacy mode
            workflow.add_edge(START, "task_plan")
            workflow.add_conditional_edges(
                "task_plan",
                self._should_execute_devices,
                {
                    "execute": "execute_device_actions",
                    "skip": "generate_audio",
                    "error": "handle_error"
                }
            )
            workflow.add_edge("execute_device_actions", "generate_audio")
            workflow.add_edge("generate_audio", "finalize_response")
            workflow.add_edge("finalize_response", END)
            workflow.add_edge("handle_error", END)

        return workflow.compile(checkpointer=self.memory)

    @observe(name="task_plan_node")
    async def _task_plan_node(self, state: AISystemState) -> AISystemState:
        """Task planning node - unified processing through task planner"""
        try:
            self.logger.info("Starting task planning")

            # Use task planner to process the request
            response, conversation_id = await self.task_planner.process_request(
                user_input=state["user_input"],
                user_id=state.get("user_id", "default_user"),
                conversation_id=state.get("session_id")
            )

            # Get conversation context from task planner
            ctx = self.task_planner.active_conversations.get(conversation_id)

            return {
                **state,
                "session_id": conversation_id,
                "context": ctx.to_dict() if ctx else {},
                "character_response": response,
                "intent_analysis": ctx.current_intent if ctx else {},
                "metadata": {
                    "unified_mode": True,
                    "timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Task planning failed: {e}")
            return {**state, "error": f"Task planning failed: {str(e)}"}

    @observe(name="analyze_intent_node")
    async def _analyze_intent_node(self, state: AISystemState) -> AISystemState:
        """Node for intent analysis"""
        try:
            self.logger.info("Starting intent analysis")

            # Load context
            context = await self._load_context(state)

            # Analyze intent
            intent_result = await self.intent_analyzer.analyze_intent(
                state["user_input"],
                context
            )

            return {
                **state,
                "context": context.to_dict() if context else {},
                "intent_analysis": intent_result,
                "metadata": {
                    "intent_analysis_timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Intent analysis failed: {e}")
            return {**state, "error": f"Intent analysis failed: {str(e)}"}

    @observe(name="execute_device_actions_node")
    async def _execute_device_actions_node(self, state: AISystemState) -> AISystemState:
        """Node for device action execution with familiarity check"""
        try:
            self.logger.info("Executing device actions")

            intent_analysis = state.get("intent_analysis", {})
            context = await self._load_context(state)
            if not context:
                return {**state, "error": "Failed to load context"}
            familiarity = context.familiarity_score

            # Log familiarity check for devices
            if intent_analysis.get("involves_hardware"):
                device = intent_analysis.get("device")
                action = intent_analysis.get("action")
                self.logger.info(f"Device control requested: {device} -> {action}")
                self.logger.info(f"User familiarity: {familiarity}/100 (min required: 40)")

                familiarity_check = intent_analysis.get("familiarity_check", "unknown")
                if familiarity < 40:
                    self.logger.info(f"Device control request denied due to insufficient familiarity")
                    return {
                        **state,
                        "device_actions": [{
                            "success": False,
                            "reason": "insufficient_familiarity",
                            "device": device,
                            "action": action
                        }],
                        "metadata": {
                            **state.get("metadata", {}),
                            "device_actions_timestamp": datetime.now().isoformat(),
                            "familiarity_check": "failed"
                        }
                    }
                else:
                    self.logger.info(f"Device control authorized - familiarity check passed")

            # Check if there are device actions to execute
            if not intent_analysis.get("involves_hardware"):
                return {**state, "device_actions": []}

            # Execute device actions through controller
            results = []
            device_result = await self.device_controller.process_device_intent(
                intent_analysis,
                context
            )

            if device_result.get("success"):
                results.append(device_result)
                self.logger.info(f"Device action executed successfully: {device_result}")

            return {
                **state,
                "device_actions": results,
                "metadata": {
                    **state.get("metadata", {}),
                    "device_actions_timestamp": datetime.now().isoformat(),
                    "familiarity_check": "passed"
                }
            }

        except Exception as e:
            self.logger.error(f"Device action execution failed: {e}")
            return {**state, "error": f"Device action execution failed: {str(e)}"}

    @observe(name="generate_character_response_node")
    async def _generate_character_response_node(self, state: AISystemState) -> AISystemState:
        """Node for character response generation"""
        try:
            self.logger.info("Generating character response")

            # Prepare context for character system
            context = await self._load_context(state)
            if not context:
                return {**state, "error": "Failed to load context for character system"}

            # Update context with current state
            context.user_input = state["user_input"]
            if state.get("intent_analysis"):
                context.current_intent = state["intent_analysis"]

            # Prepare response data
            device_actions = state.get("device_actions", [])
            
            # Check if there are any familiarity-related rejections
            has_familiarity_rejection = any(
                action.get("reason") == "insufficient_familiarity" 
                for action in device_actions
            )
            
            response_data = {
                "intent_analysis": state.get("intent_analysis", {}),
                "device_actions": device_actions,
                "insufficient_familiarity": has_familiarity_rejection
            }

            # Generate character response
            response = await self.character_system.generate_response(
                context,
                response_data
            )

            return {
                **state,
                "character_response": response,
                "metadata": {
                    **state.get("metadata", {}),
                    "character_response_timestamp": datetime.now().isoformat()
                }
            }

        except Exception as e:
            self.logger.error(f"Character response generation failed: {e}")
            return {**state, "error": f"Character response generation failed: {str(e)}"}

    @observe(name="finalize_response_node")
    async def _finalize_response_node(self, state: AISystemState) -> AISystemState:
        """Node for finalizing the response"""
        try:
            self.logger.info("Finalizing response")

            # Create final response structure (filter sensitive information)
            device_actions = state.get("device_actions", []) or []
            # Remove sensitive familiarity information from device actions
            filtered_device_actions = []
            for action in device_actions if device_actions else []:
                filtered_action = {
                    "success": action.get("success", False),
                    "device": action.get("device"),
                    "action": action.get("action")
                }
                # Only add reason if it's not familiarity-related
                reason = action.get("reason")
                if reason and reason != "insufficient_familiarity":
                    filtered_action["reason"] = reason
                filtered_device_actions.append(filtered_action)
            
            final_response = {
                "response": state.get("character_response", "I apologize, but I couldn't generate a response."),
                "intent_analysis": state.get("intent_analysis", {}),
                "device_actions": filtered_device_actions,
                "audio": None,
                "session_id": state.get("session_id"),
                "timestamp": datetime.now().isoformat(),
                "metadata": state.get("metadata", {})
            }

            audio_data = state.get("audio_data")
            if audio_data:
                audio_result = state.get("audio_generation_result", {}) or {}
                voice_value = audio_result.get("voice") or getattr(self.agora_tts, "default_voice", None)
                final_response["audio"] = {
                    "data": audio_data,
                    "format": audio_result.get("format", "base64_mp3"),
                    "voice": voice_value,
                    "timestamp": audio_result.get("timestamp") or datetime.now().isoformat()
                }
            else:
                final_response.pop("audio", None)

            # Update context after successful processing
            if state.get("context") and not state.get("error"):
                await self._update_context(state)

            return {
                **state,
                "final_response": json.dumps(final_response, indent=2)
            }

        except Exception as e:
            self.logger.error(f"Response finalization failed: {e}")
            return {**state, "error": f"Response finalization failed: {str(e)}"}

    @observe(name="handle_error_node")
    async def _handle_error_node(self, state: AISystemState) -> AISystemState:
        """Node for error handling"""
        error_message = state.get("error", "Unknown error occurred")
        self.logger.error(f"Workflow error: {error_message}")

        error_response = {
            "response": "I apologize, but I encountered an error while processing your request. Please try again.",
            "error": error_message,
            "session_id": state.get("session_id"),
            "timestamp": datetime.now().isoformat()
        }

        return {
            **state,
            "final_response": json.dumps(error_response, indent=2)
        }

    def _should_execute_devices(self, state: AISystemState) -> str:
        """Conditional edge function to determine if device actions should be executed"""
        if state.get("error"):
            return "error"

        intent_analysis = state.get("intent_analysis", {})

        # Check if hardware operation is requested
        involves_hardware = intent_analysis.get("involves_hardware", False)

        if involves_hardware:
            device = intent_analysis.get("device")
            self.logger.info(f"Device operation detected: {device}")
            return "execute"
        else:
            self.logger.info("No device operations needed")
            return "skip"

    async def _load_context(self, state: AISystemState) -> Optional[SystemContext]:
        """Load system context with user familiarity"""
        try:
            # Create or get session context
            session_id = state.get("session_id")
            user_id = state.get("user_id")
            
            if session_id:
                context = self.context_manager.create_session(session_id)
            else:
                context = self.context_manager.get_context()
            
            # Load user familiarity from database
            if user_id:
                familiarity = self.db_service.get_user_familiarity(user_id)
                context.familiarity_score = familiarity
                self.logger.info(f"Loaded user familiarity: {familiarity}/100")
            else:
                # Use default familiarity for anonymous users
                context.familiarity_score = self.config.system.default_familiarity_score
                self.logger.info(f"Using default familiarity: {context.familiarity_score}/100")
            
            return context
        except Exception as e:
            self.logger.error(f"Context loading failed: {e}")
            return None

    async def _update_context(self, state: AISystemState):
        """Update system context after processing"""
        try:
            context_dict = state.get("context", {})
            if context_dict:
                # Update the context manager with new information
                self.context_manager.update_context(**context_dict)
        except Exception as e:
            self.logger.error(f"Context update failed: {e}")

    @observe(name="langgraph_workflow")
    async def process_message(self, user_input: str, user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """Process a user message through the LangGraph workflow with Langfuse tracing"""
        if not LANGGRAPH_AVAILABLE:
            raise RuntimeError("LangGraph is not available. Please install langgraph package.")

        # Create initial state
        initial_state = AISystemState(
            user_input=user_input,
            user_id=user_id or str(uuid.uuid4()),
            session_id=session_id or str(uuid.uuid4()),
            context=None,
            intent_analysis=None,
            device_actions=None,
            character_response=None,
            audio_data=None,
            audio_generation_result=None,
            final_response=None,
            error=None,
            metadata={}
        )

        # Execute workflow with Langfuse tracing
        thread_id = session_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        # No need to manually start trace - @observe decorators will handle it

        try:
            result = await self.workflow.ainvoke(initial_state, config)

            # Parse final response
            final_response_str = result.get("final_response", "{}")
            final_response = json.loads(final_response_str)

            # Score the trace if Langfuse is enabled
            if self.langfuse_enabled and self.langfuse_client:
                try:
                    # Update current trace with metadata
                    self.langfuse_client.update_current_trace(
                        user_id=user_id,
                        session_id=session_id,
                        output=final_response
                    )

                    # Score based on success/failure
                    if not result.get("error"):
                        self.langfuse_client.score_current_trace(
                            name="completion",
                            value=1.0,
                            comment="Workflow completed successfully"
                        )
                    else:
                        self.langfuse_client.score_current_trace(
                            name="completion",
                            value=0.0,
                            comment=f"Workflow failed: {result.get('error')}"
                        )
                except Exception as e:
                    self.logger.warning(f"Failed to update trace: {e}")

            return final_response

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return {
                "response": "I apologize, but I encountered an error while processing your request.",
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }

    async def get_workflow_state(self, session_id: str) -> Optional[Dict]:
        """Get the current workflow state for a session"""
        if not LANGGRAPH_AVAILABLE:
            return None

        try:
            config = {"configurable": {"thread_id": session_id}}
            state = await self.workflow.aget_state(config)
            return state.values if state else None
        except Exception as e:
            self.logger.error(f"Failed to get workflow state: {e}")
            return None

    # Planner-based workflow nodes
    @observe(name="make_plan_node")
    async def _make_plan_node(self, state: AISystemState) -> AISystemState:
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
    async def _execute_plan_node(self, state: AISystemState) -> AISystemState:
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
    async def _generate_audio_node(self, state: AISystemState) -> AISystemState:
        """Audio generation node - converts text to speech"""
        try:
            self.logger.info("Generating audio output")

            character_response = state.get("character_response", "")
            if not character_response:
                return {**state, "audio_data": None, "audio_generation_result": None}

            if not self.agora_tts.enabled:
                self.logger.info("TTS disabled; skipping audio generation")
                return {
                    **state,
                    "audio_data": None,
                    "audio_generation_result": {
                        "success": False,
                        "error": "TTS disabled"
                    },
                    "metadata": {
                        **state.get("metadata", {}),
                        "audio_enabled": False
                    }
                }

            # Generate audio using TTS service
            audio_result = await self.tool_executor.execute_agora_tts(
                character_response,
                voice=None
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

    def _should_execute_plan(self, state: AISystemState) -> str:
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

    def _should_generate_audio(self, state: AISystemState) -> str:
        """Conditional edge for audio generation"""
        if state.get("error"):
            return "error"

        # Check if audio generation is needed and enabled
        if self.agora_tts.enabled and state.get("character_response"):
            return "generate_audio"
        else:
            return "skip_audio"

# Compatibility function for existing code
async def create_langraph_system(config: Config = None) -> LangGraphHomeAISystem:
    """Create and initialize LangGraph-based Home AI System"""
    system = LangGraphHomeAISystem(config)
    return system

if __name__ == "__main__":
    async def test_workflow():
        """Test the LangGraph workflow"""
        print("🧪 Testing LangGraph Workflow")
        print("=" * 50)

        try:
            # Initialize system
            config = load_config()
            system = await create_langraph_system(config)

            # Test message
            result = await system.process_message(
                "Turn on the living room lights",
                user_id="test_user",
                session_id="test_session"
            )

            print("✅ Workflow test completed!")
            print(f"Result: {json.dumps(result, indent=2)}")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(test_workflow())
