from functools import lru_cache
from pydantic import Field
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
                           env_file=PROJECT_ROOT / ".env",
                           extra="ignore"
    )

    host: str = "127.0.0.1"
    port: int = 8000
    database_url: str = "sqlite:///data/app.db"
    ollama_url: str = "http://ollama:11434"
    whatsapp_api_url: str = "https://localhost:3000"
    whatsapp_ssl_path: str = "mkcert/rootCA.pem"
    webhook_api_key: str = Field(min_length=8, default="change-me")
    log: str = "DEBUG"
    max_tool_iterations: int = 5
    device: str = "cpu"
    embed_model: str = "nomic-embed-text"
    model: str = "qwen3:8b"
    top_k: int = 40
    top_p: float = 0.9
    temperature: float = 0.7
    voice_file: str = "voice-file.wav"
    voice_lang: str = "tr"

    @property
    def database_url_expanded(self) -> str:
        """Veritabanı yolunu genişlet"""
        if self.database_url.startswith("sqlite:///"):
            db_path = PROJECT_ROOT / self.database_url.replace("sqlite:///", "")
            return f"sqlite:///{db_path}"
        return self.database_url

@lru_cache
def get_settings() -> Settings:
    return Settings()