from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str

    r2_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str = "frameai"
    r2_public_domain: str = "https://r2.frameai.in"

    fal_api_key: str = ""
    redis_url: str = "redis://localhost:6379"
    session_secret: str

    # Stored as comma-separated string so pydantic-settings doesn't JSON-parse it.
    # Use get_allowed_origins() for the parsed list.
    allowed_origins: str = "http://localhost:3000"

    def get_allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
