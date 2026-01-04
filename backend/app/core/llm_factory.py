from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

class LLMFactory:
    @staticmethod
    def create_llm(provider: str = None, model_name: str = None, temperature: float = 0.0):
        """
        Returns an LLM instance. 
        If 'provider' is passed, it overrides the global settings.
        """
        # Default to settings if not provided
        current_provider = (provider or settings.LLM_PROVIDER).lower()
        
        if current_provider == "openai":
            return ChatOpenAI(
                model=model_name or settings.OPENAI_MODEL_NAME,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=temperature
            )
        elif current_provider == "groq":
            return ChatGroq(
                model=model_name or settings.GROQ_MODEL_NAME,
                groq_api_key=settings.GROQ_API_KEY,
                temperature=temperature
            )
        elif current_provider == "anthropic":
            return ChatAnthropic(
                model=model_name or settings.ANTHROPIC_MODEL_NAME,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                temperature=temperature
            )
        elif current_provider == "google":
            return ChatGoogleGenerativeAI(
                model=model_name or settings.GOOGLE_FLASH_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=temperature
            )
        elif current_provider == "deepseek":
            return ChatOpenAI(
                model=model_name or settings.DEEPSEEK_MODEL_NAME,
                openai_api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
                temperature=temperature
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {current_provider}")