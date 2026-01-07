from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str
    # LLM
    groq_api_key: str
    # Embeddings / RAG
    embedding_model: str
    vector_db_path: str
    huggingface_api_key: str | None = None
    # Web Search
    tavily_api_key: str | None = None
    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"  


settings = Settings()
