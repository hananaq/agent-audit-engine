import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AgentAudit Engine"
    
    # lite vs pro
    TIER: str = os.getenv("TIER", "lite") 
    
    @property
    def LLM_PROVIDER(self) -> str:
        # Default to groq for lite tier if not explicitly set
        env_provider = os.getenv("LLM_PROVIDER")
        if env_provider:
            return env_provider
        return "groq" if self.TIER == "lite" else "openai"
    
    # Models
    # --- Pro Tier Judges ---
    # Judge A (Pro): OpenAI GPT-4o
    OPENAI_MODEL_NAME: str = "gpt-4o"
    # Judge B (Pro): Anthropic Claude 4.5 Sonnet
    ANTHROPIC_MODEL_NAME: str = "claude-sonnet-4-5"
    # Judge C (Pro): Google Gemini 1.5 Pro
    GOOGLE_PRO_MODEL: str = "gemini-pro-latest"
    
    # --- Free Tier Judges ---
    # Judge A (Free): Groq Llama 3.1 8B
    GROQ_MODEL_NAME: str = "llama-3.1-8b-instant"
    # Judge B (Free): Google Gemini 1.5 Flash
    GOOGLE_FLASH_MODEL: str = "gemini-flash-latest"
    # Judge C (Free): DeepSeek V3
    DEEPSEEK_MODEL_NAME: str = "deepseek-chat"

    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # Rate Limiting
    THROTTLE_DELAY: float = 1.0  # Seconds between probes

    # CORS
    CORS_ALLOW_ORIGINS: list[str] = ["*"]

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    @property
    def SWAP_DATABASE_URL(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.TIER == "lite":
            return "sqlite:///./agentaudit.db"
        return "postgresql://user:password@localhost/agentaudit"

    model_config = SettingsConfigDict(
        env_file=(
            Path(__file__).parent.parent.parent / ".env",
            Path(__file__).parent.parent.parent / ".env.secret"
        ),
        extra="ignore"
    )

settings = Settings()
