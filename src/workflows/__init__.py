"""
Workflow orchestration
"""

from .langraph_workflow import LangGraphHomeAISystem, create_langraph_system
from .traditional_workflow import HomeAISystem
from .optimized_workflow import OptimizedHomeAISystem, create_optimized_system

__all__ = [
    "LangGraphHomeAISystem",
    "create_langraph_system",
    "HomeAISystem",
    "OptimizedHomeAISystem",
    "create_ai_system",
    "create_optimized_system"
]

# Factory function - defaults to LangGraph with optimization
async def create_ai_system(config = None, use_langgraph: bool = True):
    """
    Create AI system with LangGraph workflow (optimized)
    
    Args:
        config: Configuration object
        use_langgraph: Use LangGraph workflow (default: True, recommended)
    
    Returns:
        AI system instance
    
    Note: LangGraph workflow now uses UnifiedResponder internally for 50% faster responses
    """
    from ..utils.config import load_config
    
    config = config or load_config()
    
    if use_langgraph:
        try:
            from .langraph_workflow import LANGGRAPH_AVAILABLE
            if LANGGRAPH_AVAILABLE:
                print("🔗 Using LangGraph Workflow (with Optimized Response Generation)")
                return await create_langraph_system(config)
        except ImportError:
            pass
    
    # Fallback to traditional
    print("⚠️ LangGraph not available, using Traditional Workflow")
    return HomeAISystem(config)