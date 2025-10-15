"""
Configuration management for the Smart Home AI Assistant
"""
import json
import os
from typing import Optional
from dataclasses import dataclass, field
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
class GeminiConfig:
    """Google Gemini API configuration"""
    api_key: str
    model: str = "gemini-2.5-flash"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta/"
    max_tokens: int = 100000
    timeout: int = 60

@dataclass
class LLMConfig:
    """General LLM provider configuration"""
    provider: str = "gemini"  # Options: anthropic, gemini
    enabled: bool = True

@dataclass
class SystemConfig:
    """System-wide configuration"""
    debug: bool = False
    log_level: str = "INFO"
    api_port: int = 10030
    conversation_timeout_minutes: int = 30
    max_active_conversations: int = 1000
    cleanup_interval_minutes: int = 10
    default_familiarity_score: int = 25
    min_familiarity_for_hardware: int = 40
    
    # Conversation context configuration
    max_conversation_turns: int = 20  # Maximum turns to keep in memory for LLM context
    max_history_storage: int = 100   # Maximum turns to store in database (unlimited if -1)
    conversation_context_window: int = 8000  # Token limit for conversation context

    # Temporary audio upload
    temp_upload_enabled: bool = True
    temp_upload_host: str = "https://catbox.moe"
    public_base_url: Optional[str] = None

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


@dataclass
class ElevenLabsTTSConfig:
    """ElevenLabs Text-to-Speech configuration"""
    api_key: str
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default to Rachel's public voice ID
    model: str = "eleven_multilingual_v2"
    output_format: str = "mp3_44100_128"
    voice_settings: dict = field(default_factory=dict)
    style_preset: Optional[str] = None
    optimize_streaming_latency: Optional[int] = None
    base_url: str = "https://api.elevenlabs.io"
    enabled: bool = True


@dataclass
class TTSConfig:
    """General text-to-speech provider configuration"""
    provider: str = "openai"
    enabled: bool = True
    default_voice: Optional[str] = None
    audio_format: str = "mp3"

class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.database = self._load_database_config()
        self.langfuse = self._load_langfuse_config()
        self.llm = self._load_llm_config()
        self.anthropic = self._load_anthropic_config()
        self.gemini = self._load_gemini_config()
        self.system = self._load_system_config()
        self.vector_search = self._load_vector_search_config()
        self.tts = self._load_tts_config()
        self.openai_tts = self._load_openai_tts_config()
        self.elevenlabs_tts = self._load_elevenlabs_tts_config()
    
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
    
    def _load_llm_config(self) -> LLMConfig:
        """Centralized LLM provider configuration (code-controlled)"""
        return LLMConfig(
            provider="gemini",
            enabled=True
        )
    
    def _load_anthropic_config(self) -> AnthropicConfig:
        """Anthropic configuration: API key may come from env; system settings are code-controlled."""
        api_key = os.getenv("ANTHROPIC_API_KEY") or ""
        return AnthropicConfig(
            api_key=api_key,
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            timeout=60
        )
    
    def _load_gemini_config(self) -> GeminiConfig:
        """Gemini configuration: API key may come from env; system settings are code-controlled."""
        api_key = os.getenv("GEMINI_API_KEY", "")
        return GeminiConfig(
            api_key=api_key,
            model="gemini-2.5-flash",
            base_url="https://generativelanguage.googleapis.com/v1beta/",
            max_tokens=10000,
            timeout=60
        )
    
    def _load_system_config(self) -> SystemConfig:
        """Centralized system configuration (code-controlled, no .env overrides)."""
        return SystemConfig()
    
    def _load_vector_search_config(self) -> VectorSearchConfig:
        """Centralized vector search configuration (code-controlled)."""
        return VectorSearchConfig()

    def _load_tts_config(self) -> TTSConfig:
        """Centralized TTS configuration (code-controlled)."""
        return TTSConfig()

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

    def _load_elevenlabs_tts_config(self) -> ElevenLabsTTSConfig:
        """Load ElevenLabs TTS configuration from environment variables"""
        api_key = os.getenv("ELEVENLABS_API_KEY")

        if not api_key:
            return ElevenLabsTTSConfig(
                api_key="",
                enabled=False
            )

        # Try to load from config file first
        config_file_path = Path("config/elevenlabs_config.json")
        if config_file_path.exists():
            try:
                import json
                with open(config_file_path, 'r') as f:
                    config_data = json.load(f)
                    voice_id = config_data.get("voice_id", os.getenv("ELEVENLABS_VOICE_ID", "rWArYo7a2NWuBYf5BE4V"))
                    model = config_data.get("model", os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5"))
                    print(f"✓ Loaded ElevenLabs config from config/elevenlabs_config.json")
            except Exception as e:
                print(f"⚠️  Failed to load ElevenLabs config file: {e}, using environment variables")
                voice_id = os.getenv("ELEVENLABS_VOICE_ID", "rWArYo7a2NWuBYf5BE4V")
                model = os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5")
        else:
            voice_id = os.getenv("ELEVENLABS_VOICE_ID", "rWArYo7a2NWuBYf5BE4V")
            model = os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5")
        output_format = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128")
        base_url = os.getenv("ELEVENLABS_API_BASE", "https://api.elevenlabs.io").rstrip("/") or "https://api.elevenlabs.io"

        voice_settings_payload = os.getenv("ELEVENLABS_VOICE_SETTINGS")
        voice_settings = {}
        if voice_settings_payload:
            try:
                voice_settings = json.loads(voice_settings_payload)
            except json.JSONDecodeError:
                print("⚠️ Warning: ELEVENLABS_VOICE_SETTINGS is not valid JSON. Ignoring value.")

        style_preset = os.getenv("ELEVENLABS_STYLE_PRESET")
        optimize_latency_env = os.getenv("ELEVENLABS_OPTIMIZE_STREAMING_LATENCY")
        optimize_latency = None
        if optimize_latency_env is not None and optimize_latency_env.strip():
            try:
                optimize_latency = int(optimize_latency_env)
            except ValueError:
                print("⚠️ Warning: ELEVENLABS_OPTIMIZE_STREAMING_LATENCY must be an integer. Ignoring value.")

        return ElevenLabsTTSConfig(
            api_key=api_key,
            voice_id=voice_id,
            model=model,
            output_format=output_format,
            voice_settings=voice_settings,
            style_preset=style_preset,
            optimize_streaming_latency=optimize_latency,
            base_url=base_url,
            enabled=os.getenv("ELEVENLABS_TTS_ENABLED", "true").lower() == "true"
        )
    
    def validate(self) -> bool:
        """Validate configuration"""
        errors = []
        
        # Check required configurations based on LLM provider
        if self.llm.provider == "anthropic":
            if not self.anthropic.api_key:
                errors.append("ANTHROPIC_API_KEY is required when using Anthropic provider")
        elif self.llm.provider == "gemini":
            if not self.gemini.api_key:
                errors.append("GEMINI_API_KEY is required when using Gemini provider")
        else:
            errors.append(f"Unsupported LLM provider: {self.llm.provider}")
        
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
        print(f"  LLM Provider: {self.llm.provider}")
        if self.llm.provider == "anthropic":
            print(f"    Anthropic Model: {self.anthropic.model}")
        elif self.llm.provider == "gemini":
            print(f"    Gemini Model: {self.gemini.model}")
        print(f"  Debug Mode: {self.system.debug}")
        print(f"  Vector Search: {'✅ Enabled' if self.vector_search.enabled else '❌ Disabled'}")
        print(
            f"  TTS Provider: {self.tts.provider} "
            f"({'✅ Enabled' if self.tts.enabled else '❌ Disabled'})"
        )
        print(
            f"    OpenAI: {'✅' if self.openai_tts.enabled else '❌'} | "
            f"ElevenLabs: {'✅' if self.elevenlabs_tts.enabled else '❌'}"
        )

def load_config() -> Config:
    """Load and validate configuration"""
    config = Config()
    
    if not config.validate():
        raise ValueError("Configuration validation failed")
    
    return config

# Environment file template
def create_env_template():
    """Create a .env template file"""
    template = """# Smart Home AI Assistant - Secrets Template Only

# LLM API Keys (secrets only)
GEMINI_API_KEY=
ANTHROPIC_API_KEY=

# Langfuse Observability (optional)
LANGFUSE_SECRET_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com

# Database (optional - use env only if not using default SQLite)
DATABASE_URL=

# OpenAI TTS (optional secret)
OPENAI_API_KEY=
OPENAI_TTS_ENABLED=true

# ElevenLabs TTS (optional secret)
ELEVENLABS_API_KEY=
ELEVENLABS_TTS_ENABLED=true
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
