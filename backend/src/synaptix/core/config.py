from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


#class Settings(BaseSettings):
    #app_name: str = "Synaptix API"
    #environment: str = "development"
    #database_url: str
    #secret_key: str
    #access_token_expire_minutes: int = 60


class Settings(BaseSettings):
    app_environment: Literal[
        "development",
        "test",
        "staging",
        "production",
    ] = "development"

    enable_demo_auth: bool = False

    frontend_origin: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()