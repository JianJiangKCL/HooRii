# Project Structure

```
hoorii/
├── src/                          # Main source code directory
│   ├── __init__.py
│   ├── core/                     # Core business logic
│   │   ├── __init__.py
│   │   ├── intent_analyzer.py    # Intent analysis logic
│   │   ├── device_controller.py  # Device control logic
│   │   ├── character_system.py   # Character response system
│   │   └── context_manager.py    # Context management
│   │
│   ├── workflows/                # Workflow orchestration
│   │   ├── __init__.py
│   │   ├── langraph_workflow.py  # LangGraph workflow
│   │   └── traditional_workflow.py # Traditional workflow (from main.py)
│   │
│   ├── services/                 # External services & integrations
│   │   ├── __init__.py
│   │   ├── database_service.py   # Database operations
│   │   ├── langfuse_service.py   # Langfuse integration
│   │   └── anthropic_service.py  # Anthropic API wrapper
│   │
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   ├── server.py             # FastAPI server (from api.py)
│   │   ├── routes/               # API routes
│   │   │   ├── __init__.py
│   │   │   ├── chat.py          # Chat endpoints
│   │   │   ├── users.py         # User management endpoints
│   │   │   └── devices.py       # Device management endpoints
│   │   └── schemas/              # Pydantic models
│   │       ├── __init__.py
│   │       ├── requests.py      # Request models
│   │       └── responses.py     # Response models
│   │
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   └── database.py          # SQLAlchemy models (from models.py)
│   │
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration management
│   │   └── device_simulator.py  # Device simulation utilities
│   │
│   └── main.py                   # Application entry point
│
├── tests/                        # Test files
│   ├── __init__.py
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests (from debug/)
│   │   ├── test_langraph_integration.py
│   │   └── test_langfuse_langgraph.py
│   └── fixtures/                # Test fixtures and mocks
│
├── scripts/                      # Utility scripts
│   ├── setup_env.py             # Environment setup
│   ├── start_api_server.py     # API server launcher
│   └── run_app.py              # CLI app launcher
│
├── prompts/                     # LLM prompt templates
│   ├── intent_analysis.txt
│   ├── device_controller.txt
│   └── character_responses.txt
│
├── configs/                     # Configuration files
│   ├── .env.template
│   └── logging.yaml            # Logging configuration
│
├── docs/                       # Documentation
│   ├── API.md                 # API documentation
│   ├── USER_GUIDE.md          # User guide
│   └── DEVELOPMENT.md         # Development guide
│
├── data/                      # Data files
│   ├── contexts/             # Context saves
│   └── hoorii.db            # SQLite database
│
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project metadata
├── README.md               # Project README
└── .gitignore             # Git ignore file
```

## Benefits of this structure:
1. **Clear separation of concerns** - Each folder has a specific purpose
2. **Modular architecture** - Easy to find and modify components
3. **Scalability** - Easy to add new features in appropriate locations
4. **Testing** - Separated test directory with proper organization
5. **Configuration** - Centralized configuration management
6. **Documentation** - Dedicated docs folder