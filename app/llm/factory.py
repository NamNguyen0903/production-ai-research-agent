from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.core.config import Settings


def create_chat_model(
    settings: Settings,
) -> BaseChatModel:
    if settings.llm_provider == "openai":
        if (
            settings.openai_api_key is None
            or not settings.openai_api_key.get_secret_value().strip()
        ):
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")

        return ChatOpenAI(
            model=settings.llm_model,
            temperature=0,
            api_key=settings.openai_api_key.get_secret_value(),
        )

    if settings.llm_provider == "google":
        if (
            settings.google_api_key is None
            or not settings.google_api_key.get_secret_value().strip()
        ):
            raise ValueError("GOOGLE_API_KEY is required when LLM_PROVIDER=google.")

        return ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=0,
            google_api_key=settings.google_api_key.get_secret_value(),
        )

    raise ValueError("create_chat_model() cannot be used with LLM_PROVIDER=mock.")
