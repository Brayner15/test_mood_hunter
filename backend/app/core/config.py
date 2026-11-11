from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Tablero de Solicitudes API"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    database_url: str = (
        "mysql+pymysql://app:apppass@localhost:3307/solicitudes?charset=utf8mb4"
    )

    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_timeout_seconds: float = 8.0
    llm_max_retries: int = 1
    llm_cache_ttl_seconds: int = 300

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
