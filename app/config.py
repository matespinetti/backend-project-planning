from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Cloud Persistence API
    CLOUD_API_URL: str
    CLOUD_API_TIMEOUT: int = 30  # seconds
    CLOUD_API_JWT_SECRET: str
    CLOUD_API_JWT_ALGORITHM: str = "HS256"

    # Bonita BPM
    BONITA_URL: str
    BONITA_USERNAME: str
    BONITA_PASSWORD: str
    BONITA_PROCESS_NAME: str
    BONITA_PROCESS_VERSION: str = "1.0"

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "ProjectPlanning Proxy API"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Create and cache a singleton Settings instance."""
    return Settings()
