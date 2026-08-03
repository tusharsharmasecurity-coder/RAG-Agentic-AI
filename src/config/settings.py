from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the entire project.
    Reads values automatically from the .env file.
    """

    # ------------------------
    # Database Configuration
    # ------------------------

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # ------------------------
    # AI Providers
    # ------------------------

    GROQ_API_KEY: str | None = None
    NVIDIA_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    LANGSMITH_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()