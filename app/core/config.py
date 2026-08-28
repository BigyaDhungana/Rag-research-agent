from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    gemini_model: str = "gemini-3.6-flash"
    gemini_api_key: str

    @property
    def database_url(self) -> str:
        # URL-encode user/password: either can legally contain characters
        # (@, :, /, ?, #, %) that are reserved in URL syntax. Without this,
        # a password like "Apiwatch@test123" gets misparsed — the URL parser
        # splits credentials-from-host on the FIRST "@", so part of the
        # password gets swallowed into what it thinks is the hostname.
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        return f"postgresql+psycopg2://{user}:{password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


@lru_cache
def get_settings() -> Settings:
    """
    Cached so we parse the environment once per process for consistencey
    """
    return Settings()


settings = get_settings()
