"""Centralized, environment-backed runtime settings."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_name: str = os.getenv("DB_NAME", "delhivery_ai")
    db_user: str | None = os.getenv("DB_USER")
    db_password: str | None = os.getenv("DB_PASSWORD")
    database_url: str | None = os.getenv("DATABASE_URL")
    redis_url: str | None = os.getenv("REDIS_URL")
    embedding_device: str = os.getenv("EMBEDDING_DEVICE", "auto")
    embedding_batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

    def require_database_credentials(self) -> tuple[str, str]:
        if not self.db_user or not self.db_password:
            raise RuntimeError(
                "Database credentials are not configured. Set DATABASE_URL or DB_USER and DB_PASSWORD in .env."
            )
        return self.db_user, self.db_password


settings = Settings()
