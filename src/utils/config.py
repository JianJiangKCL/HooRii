"""
Configuration management for the Smart Home AI Assistant
"""
import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    url: str
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_pre_ping: bool = True

@dataclass
class LangfuseConfig:
    """Langfuse configuration settings"""
    secret_key: str
    public_key: str
    host: str = "https://cloud.langfuse.com"
    enabled: bool = True

@dataclass
class AnthropicConfig:
    """Anthropic Claude API configuration"""
    api_key: str
    model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 1000
    timeout: int = 60

@dataclass
class SystemConfig:
    """System-wide configuration"""
    debug: bool = False
    log_level: str = "INFO"
    conversation_timeout_minutes: int = 30
    max_active_conversations: int = 1000
    cleanup_interval_minutes: int = 10
    default_familiarity_score: int = 25
    min_familiarity_for_hardware: int = 40
    
    # Conversation context configuration
    max_conversation_turns: int = 20  # Maximum turns to keep in memory for LLM context
    max_history_storage: int = 100   # Maximum turns to store in database (unlimited if -1)
    conversation_context_window: int = 8000  # Token limit for conversation context

@dataclass
class VectorSearchConfig:
    """Vector search configuration for user memories"""
    enabled: bool = False  # Will implement later
    provider: str = "sentence_transformers"  # or "openai"
    model_name: str = "all-MiniLM-L6-v2"
    dimension: int = 384

@dataclass
class OpenAITTSConfig:
    """OpenAI Text-to-Speech configuration"""
    api_key: str
    model: str = "gpt-4o-mini-tts"
    default_voice: str = "alloy"
    audio_format: str = "mp3"
    base_url: str = "https://api.openai.com"
    enabled: bool = True

class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.database = self._load_database_config()
        self.langfuse = self._load_langfuse_config()
        self.anthropic = self._load_anthropic_config()
        self.system = self._load_system_config()
        self.vector_search = self._load_vector_search_config()
        self.openai_tts = self._load_openai_tts_config()
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment variables"""
        # Default to SQLite for development, PostgreSQL for production
        default_url = "sqlite:///./hoorii.db"
        
        # Check for PostgreSQL configuration
        if all([
            os.getenv("DB_HOST"),
            os.getenv("DB_NAME"),
            os.getenv("DB_USER"),
            os.getenv("DB_PASSWORD")
        ]):
            host = os.getenv("DB_HOST", "localhost")
            port = os.getenv("DB_PORT", "5432")
            name = os.getenv("DB_NAME")
            user = os.getenv("DB_USER")
            password = os.getenv("DB_PASSWORD")
            default_url = f"postgresql://{user}:{password}@{host}:{port}/{name}"
        
        return DatabaseConfig(
            url=os.getenv("DATABASE_URL", default_url),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10"))
        )
    
    def _load_langfuse_config(self) -> LangfuseConfig:
        """Load Langfuse configuration from environment variables"""
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        
        if not secret_key or not public_key:
            print("⚠️ Warning: Langfuse keys not configured. Observability will be disabled.")
            return LangfuseConfig(
                secret_key="",
                public_key="",
                enabled=False
            )
        
        return LangfuseConfig(
            secret_key=secret_key,
            public_key=public_key,
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            enabled=True
        )
    
    def _load_anthropic_config(self) -> AnthropicConfig:
        """Load Anthropic configuration from environment variables"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        return AnthropicConfig(
            api_key=api_key,
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "1000")),
            timeout=int(os.getenv("ANTHROPIC_TIMEOUT", "60"))
        )
    
    def _load_system_config(self) -> SystemConfig:
        """Load system configuration from environment variables"""
        return SystemConfig(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            conversation_timeout_minutes=int(os.getenv("CONVERSATION_TIMEOUT_MINUTES", "30")),
            max_active_conversations=int(os.getenv("MAX_ACTIVE_CONVERSATIONS", "1000")),
            cleanup_interval_minutes=int(os.getenv("CLEANUP_INTERVAL_MINUTES", "10")),
            default_familiarity_score=int(os.getenv("DEFAULT_FAMILIARITY_SCORE", "25")),
            min_familiarity_for_hardware=int(os.getenv("MIN_FAMILIARITY_FOR_HARDWARE", "40")),
            
            # Conversation context configuration
            max_conversation_turns=int(os.getenv("MAX_CONVERSATION_TURNS", "20")),
            max_history_storage=int(os.getenv("MAX_HISTORY_STORAGE", "100")),
            conversation_context_window=int(os.getenv("CONVERSATION_CONTEXT_WINDOW", "8000"))
        )
    
    def _load_vector_search_config(self) -> VectorSearchConfig:
        """Load vector search configuration from environment variables"""
        return VectorSearchConfig(
            enabled=os.getenv("VECTOR_SEARCH_ENABLED", "false").lower() == "true",
            provider=os.getenv("VECTOR_SEARCH_PROVIDER", "sentence_transformers"),
            model_name=os.getenv("VECTOR_SEARCH_MODEL", "all-MiniLM-L6-v2"),
            dimension=int(os.getenv("VECTOR_SEARCH_DIMENSION", "384"))
        )

    def _load_openai_tts_config(self) -> OpenAITTSConfig:
        """Load OpenAI TTS configuration from environment variables"""
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GPT_TTS_API_KEY")

        if not api_key:
            return OpenAITTSConfig(
                api_key="",
                enabled=False
            )

        model = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
        voice = os.getenv("OPENAI_TTS_VOICE", "alloy")
        audio_format = os.getenv("OPENAI_TTS_FORMAT", "mp3")
        base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com").rstrip("/") or "https://api.openai.com"

        return OpenAITTSConfig(
            api_key=api_key,
            model=model,
            default_voice=voice,
            audio_format=audio_format,
            base_url=base_url,
            enabled=os.getenv("OPENAI_TTS_ENABLED", "true").lower() == "true"
        )
    
    def validate(self) -> bool:
        """Validate configuration"""
        errors = []
        
        # Check required configurations
        if not self.anthropic.api_key:
            errors.append("ANTHROPIC_API_KEY is required")
        
        # Database URL validation
        if not self.database.url:
            errors.append("DATABASE_URL is required")
        
        if errors:
            for error in errors:
                print(f"❌ Configuration Error: {error}")
            return False
        
        return True
    
    def print_config(self):
        """Print current configuration (without sensitive data)"""
        print("🔧 Configuration:")
        print(f"  Database: {self.database.url.split('://', 1)[0]}://***")
        print(f"  Langfuse: {'✅ Enabled' if self.langfuse.enabled else '❌ Disabled'}")
        print(f"  Anthropic Model: {self.anthropic.model}")
        print(f"  Debug Mode: {self.system.debug}")
        print(f"  Vector Search: {'✅ Enabled' if self.vector_search.enabled else '❌ Disabled'}")
        print(f"  OpenAI TTS: {'✅ Enabled' if self.openai_tts.enabled else '❌ Disabled'}")

def load_config() -> Config:
    """Load and validate configuration"""
    config = Config()
    
    if not config.validate():
        raise ValueError("Configuration validation failed")
    
    return config

# Environment file template
def create_env_template():
    """Create a .env template file"""
    template = """# Smart Home AI Assistant Configuration

# Anthropic Claude API
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-sonnet-20240229
ANTHROPIC_MAX_TOKENS=1000

# Langfuse Observability (Optional but recommended)
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_HOST=https://cloud.langfuse.com

# Database Configuration
# Option 1: SQLite (Development)
DATABASE_URL=sqlite:///./hoorii.db

# Option 2: PostgreSQL (Production)
# DATABASE_URL=postgresql://username:password@localhost:5432/hoorii
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=hoorii
# DB_USER=your_db_user
# DB_PASSWORD=your_db_password
# DB_ECHO=false

# System Settings
DEBUG=false
LOG_LEVEL=INFO
CONVERSATION_TIMEOUT_MINUTES=30
MAX_ACTIVE_CONVERSATIONS=1000
CLEANUP_INTERVAL_MINUTES=10
DEFAULT_FAMILIARITY_SCORE=25
MIN_FAMILIARITY_FOR_HARDWARE=40

# Conversation Context Settings
MAX_CONVERSATION_TURNS=20         # Maximum turns to keep in LLM context
MAX_HISTORY_STORAGE=100          # Maximum turns to store in database (-1 for unlimited)
CONVERSATION_CONTEXT_WINDOW=8000 # Token limit for conversation context

# Vector Search (Future feature)
VECTOR_SEARCH_ENABLED=false
VECTOR_SEARCH_PROVIDER=sentence_transformers
VECTOR_SEARCH_MODEL=all-MiniLM-L6-v2
VECTOR_SEARCH_DIMENSION=384

# OpenAI TTS (GPT-4o-mini-tts)
OPENAI_API_KEY=your_openai_api_key
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=alloy
OPENAI_TTS_FORMAT=mp3
OPENAI_TTS_ENABLED=true
"""
    
    env_file = Path(".env.template")
    env_file.write_text(template.strip())
    print(f"✅ Created {env_file} - Copy this to .env and fill in your values")

if __name__ == "__main__":
    # Create environment template
    create_env_template()
    
    # Test configuration loading
    try:
        config = load_config()
        config.print_config()
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
