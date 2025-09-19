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

from config import Config, load_config
from database_service import DatabaseService
from context_manager import ContextManager, SystemContext
from intent_analyzer import IntentAnalyzer
from device_controller import DeviceController
from character_system import CharacterSystem
from langfuse_session_manager import LangfuseSessionManager

# State definition for LangGraph
class AISystemState(TypedDict):
    user_input: str
    user_id: Optional[str]
    session_id: Optional[str]
    context: Optional[Dict]
    intent_analysis: Optional[Dict]
    device_actions: Optional[List[Dict]]
    character_response: Optional[str]
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
        self.session_manager = LangfuseSessionManager(self.config)

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

        # Add nodes
        workflow.add_node("analyze_intent", self._analyze_intent_node)
        workflow.add_node("execute_device_actions", self._execute_device_actions_node)
        workflow.add_node("generate_character_response", self._generate_character_response_node)
        workflow.add_node("finalize_response", self._finalize_response_node)
        workflow.add_node("handle_error", self._handle_error_node)

        # Define edges
        workflow.add_edge(START, "analyze_intent")
        workflow.add_conditional_edges(
            "analyze_intent",
            self._should_execute_devices,
            {
                "execute": "execute_device_actions",
                "skip": "generate_character_response",
                "error": "handle_error"
            }
        )
        workflow.add_edge("execute_device_actions", "generate_character_response")
        workflow.add_edge("generate_character_response", "finalize_response")
        workflow.add_edge("finalize_response", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile(checkpointer=self.memory)

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
        """Node for device action execution"""
        try:
            self.logger.info("Executing device actions")

            intent_analysis = state.get("intent_analysis", {})
            actions = intent_analysis.get("actions", [])

            if not actions:
                return {**state, "device_actions": []}

            # Execute device actions
            results = []
            context = self.context_manager.get_context()

            # Process the entire intent through device controller
            device_result = await self.device_controller.process_device_intent(
                intent_analysis,
                context
            )

            if device_result.get("success"):
                results.append(device_result)

            return {
                **state,
                "device_actions": results,
                "metadata": {
                    **state.get("metadata", {}),
                    "device_actions_timestamp": datetime.now().isoformat()
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
            context = self.context_manager.get_context()

            # Update context with current state
            context.user_input = state["user_input"]
            if state.get("intent_analysis"):
                context.current_intent = state["intent_analysis"]

            # Prepare response data
            response_data = {
                "intent_analysis": state.get("intent_analysis", {}),
                "device_actions": state.get("device_actions", [])
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

            # Create final response structure
            final_response = {
                "response": state.get("character_response", "I apologize, but I couldn't generate a response."),
                "intent_analysis": state.get("intent_analysis", {}),
                "device_actions": state.get("device_actions", []),
                "session_id": state.get("session_id"),
                "timestamp": datetime.now().isoformat(),
                "metadata": state.get("metadata", {})
            }

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
        actions = intent_analysis.get("actions", [])

        # Check if there are any device control actions
        has_device_actions = any(
            action.get("type") == "device_control"
            for action in actions
        )

        return "execute" if has_device_actions else "skip"

    async def _load_context(self, state: AISystemState) -> Optional[SystemContext]:
        """Load system context"""
        try:
            # Create or get session context
            session_id = state.get("session_id")
            if session_id:
                return self.context_manager.create_session(session_id)
            else:
                return self.context_manager.get_context()
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