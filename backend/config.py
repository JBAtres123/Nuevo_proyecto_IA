"""
DeepGrader AI — Configuración centralizada
"""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Google GenAI
    gemini_api_key: str = ""

    # MySQL
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "DeepGrader_db"

    # Almacenamiento
    upload_dir: str = "./data/examenes"
    reports_dir: str = "./data/reportes"
    materials_dir: str = "./data/materiales"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "change-me"
    cors_origins: str = "http://localhost:5173"
    groq_api_key: str = ""

    # Modelos
    model_calificador_a: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    model_calificador_b: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    model_juez: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    model_embedding: str = "gemini-embedding-001"
    model_icr: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    @property
    def db_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    def ensure_dirs(self) -> None:
        for d in [self.upload_dir, self.reports_dir, self.materials_dir]:
            Path(d).mkdir(parents=True, exist_ok=True)


# @lru_cache
#def get_settings() -> Settings:
    #return Settings()

def get_settings() -> Settings:
    return Settings()