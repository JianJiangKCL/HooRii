# LangGraph Workflow Structure Diagram

## System Architecture Overview

```mermaid
graph TB
    subgraph "Entry Point"
        A[User Input] --> B{LangGraph Available?}
        B -->|Yes| C[LangGraphHomeAISystem]
        B -->|No| D[Traditional HomeAISystem]
    end
    
    subgraph "LangGraph Workflow Selection"
        C --> E{Fast Mode?}
        E -->|Yes| F[Fast Mode Workflow]
        E -->|No| G[Original Mode Workflow]
    end
    
    subgraph "Core Components (Shared)"
        H[DatabaseService]
        I[ContextManager]
        J[IntentAnalyzer]
        K[DeviceController]
        L[CharacterSystem]
        M[FastProcessor]
        N[LangfuseSessionManager]
    end
    
    F --> H
    G --> H
    D --> H
```

## Fast Mode Workflow (Default)

```mermaid
graph TD
    subgraph "LangGraph Fast Mode State Flow"
        A[START] --> B[fast_process]
        B --> C{_should_execute_devices}
        C -->|execute| D[execute_device_actions]
        C -->|skip| E[finalize_response]
        C -->|error| F[handle_error]
        D --> E
        E --> G[END]
        F --> G
    end
    
    subgraph "State Object (AISystemState)"
        S1[user_input: str]
        S2[session_id: str]
        S3[context: Dict]
        S4[intent_analysis: Dict]
        S5[device_actions: List]
        S6[character_response: str]
        S7[final_response: str]
        S8[error: str]
        S9[metadata: Dict]
    end
    
    subgraph "Node Details"
        B1[FastProcessor.process_fast<br/>- Single LLM call<br/>- Intent + Response<br/>- JSON extraction]
        D1[DeviceController.process_device_intent<br/>- Execute device commands<br/>- Validate parameters<br/>- Update device state]
        E1[Response Formatting<br/>- Create final JSON<br/>- Update context<br/>- Add metadata]
    end
    
    B --> B1
    D --> D1
    E --> E1
```

## Original Mode Workflow

```mermaid
graph TD
    subgraph "LangGraph Original Mode State Flow"
        A[START] --> B[analyze_intent]
        B --> C{_should_execute_devices}
        C -->|execute| D[execute_device_actions]
        C -->|skip| E[generate_character_response]
        C -->|error| F[handle_error]
        D --> E
        E --> G[finalize_response]
        G --> H[END]
        F --> H
    end
    
    subgraph "Node Processing Details"
        B1[IntentAnalyzer.analyze_intent<br/>- Parse user input<br/>- Identify devices/actions<br/>- Extract parameters]
        D1[DeviceController.process_device_intent<br/>- Execute device commands<br/>- Handle device responses<br/>- Update device states]
        E1[CharacterSystem.generate_response<br/>- Generate 凌波丽 personality<br/>- Context-aware responses<br/>- Tone adaptation]
        G1[Response Assembly<br/>- Combine all data<br/>- Format final JSON<br/>- Update session state]
    end
    
    B --> B1
    D --> D1
    E --> E1
    G --> G1
```

## State Management Architecture

```mermaid
graph TB
    subgraph "Session & State Management"
        A[User Request] --> B[Thread ID Generation]
        B --> C[MemorySaver Checkpointer]
        C --> D[State Persistence]
        D --> E[Node Execution]
        E --> F[State Updates]
        F --> C
    end
    
    subgraph "Context Flow"
        G[SystemContext] --> H[ContextManager]
        H --> I[Session Creation]
        I --> J[Context Loading]
        J --> K[Node Processing]
        K --> L[Context Updates]
        L --> M[Context Persistence]
    end
    
    subgraph "Database Integration"
        N[User Data] --> O[DatabaseService]
        O --> P[Conversation History]
        P --> Q[Device States]
        Q --> R[User Preferences]
    end
    
    E --> G
    K --> N
```

## Component Integration Diagram

```mermaid
graph LR
    subgraph "LangGraph Orchestration Layer"
        A[StateGraph]
        B[Nodes]
        C[Edges]
        D[Conditional Routing]
    end
    
    subgraph "Core Business Logic"
        E[IntentAnalyzer]
        F[DeviceController]
        G[CharacterSystem]
        H[FastProcessor]
    end
    
    subgraph "Infrastructure Services"
        I[DatabaseService]
        J[ContextManager]
        K[LangfuseSessionManager]
    end
    
    subgraph "External APIs"
        L[Anthropic Claude API]
        M[Langfuse Observability]
        N[Device Simulator]
    end
    
    A --> B
    B --> E
    B --> F
    B --> G
    B --> H
    E --> I
    F --> I
    G --> I
    H --> L
    B --> J
    B --> K
    K --> M
    F --> N
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant U as User
    participant LG as LangGraph
    participant FP as FastProcessor
    participant DC as DeviceController
    participant CS as CharacterSystem
    participant DB as DatabaseService
    participant LF as Langfuse
    
    U->>LG: User Input
    LG->>LF: Start Trace
    LG->>FP: fast_process_node
    FP->>FP: Single LLM Call (Intent + Response)
    FP-->>LG: Intent Analysis + Character Response
    
    alt Device Actions Required
        LG->>DC: execute_device_actions_node
        DC->>DC: Process Device Commands
        DC-->>LG: Device Action Results
    end
    
    LG->>LG: finalize_response_node
    LG->>DB: Save Conversation
    LG->>LF: Update Trace
    LG-->>U: Final Response
```

## Error Handling Flow

```mermaid
graph TD
    subgraph "Error Detection & Handling"
        A[Any Node] --> B{Error Occurred?}
        B -->|Yes| C[handle_error_node]
        B -->|No| D[Continue Normal Flow]
        
        C --> E[Log Error Details]
        E --> F[Generate Error Response]
        F --> G[Update State with Error]
        G --> H[Return to User]
        
        D --> I[Process Next Node]
    end
    
    subgraph "Error Types"
        J[LLM API Errors]
        K[Device Control Errors]
        L[Database Errors]
        M[Context Loading Errors]
        N[Validation Errors]
    end
    
    A --> J
    A --> K
    A --> L
    A --> M
    A --> N
```

## Observability & Monitoring

```mermaid
graph TB
    subgraph "Langfuse Integration"
        A[Node Execution] --> B[@observe Decorators]
        B --> C[Automatic Tracing]
        C --> D[Performance Metrics]
        D --> E[Error Tracking]
        E --> F[User Analytics]
    end
    
    subgraph "Trace Hierarchy"
        G[Session Trace]
        G --> H[Workflow Trace]
        H --> I[Node Spans]
        I --> J[Component Spans]
        J --> K[API Call Spans]
    end
    
    subgraph "Metrics Collected"
        L[Response Time]
        M[Success Rate]
        N[Error Frequency]
        O[User Satisfaction]
        P[Device Action Success]
    end
    
    C --> G
    D --> L
    E --> N
    F --> O
```

## Configuration & Deployment

```mermaid
graph LR
    subgraph "Configuration Management"
        A[config.py] --> B[Environment Variables]
        B --> C[API Keys]
        C --> D[Model Settings]
        D --> E[Feature Flags]
    end
    
    subgraph "Deployment Options"
        F[Standalone Mode]
        G[API Server Mode]
        H[N8N Integration]
        I[Docker Container]
    end
    
    subgraph "Runtime Selection"
        J{LangGraph Available?}
        J -->|Yes| K[LangGraph Workflow]
        J -->|No| L[Traditional Workflow]
    end
    
    A --> F
    A --> G
    A --> H
    A --> I
    E --> J
```

## Performance Optimization

```mermaid
graph TD
    subgraph "Fast Mode Optimizations"
        A[Single LLM Call] --> B[Reduced Latency]
        B --> C[Lower API Costs]
        C --> D[Faster Response Time]
    end
    
    subgraph "State Management Optimizations"
        E[Memory Checkpointing] --> F[Efficient State Storage]
        F --> G[Quick Context Loading]
        G --> H[Session Persistence]
    end
    
    subgraph "Caching Strategies"
        I[Prompt Caching] --> J[Ephemeral Cache Control]
        J --> K[Reduced Token Usage]
        K --> L[Improved Performance]
    end
    
    A --> E
    E --> I
```

## Legend

- **Rectangles**: Processing nodes/components
- **Diamonds**: Decision points/conditional logic
- **Rounded Rectangles**: Start/End points
- **Dashed Lines**: Optional/conditional flows
- **Solid Lines**: Required flows
- **Subgraphs**: Logical groupings of related components

This diagram shows the complete LangGraph workflow architecture, including state management, component integration, error handling, and observability features.
