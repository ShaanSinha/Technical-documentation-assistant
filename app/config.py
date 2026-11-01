from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_directory: str = "./chroma_db"
    collection_name: str = "technical_docs"
    chunk_size: int = 900
    chunk_overlap: int = 150
    retrieval_k: int = 6
    max_retries: int = 2
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
