import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    app_name: str = "CodeVoyager"
    environment: str = os.getenv("ENVIRONMENT", "development")
    host: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    port: int = int(os.getenv("BACKEND_PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    workspace: Path = Path(
        os.getenv("CODEVOYAGER_WORKSPACE", str(PROJECT_ROOT / "workspace"))
    ).expanduser()
    database_path: Path = Path(
        os.getenv(
            "CODEVOYAGER_DATABASE_PATH",
            str(PROJECT_ROOT / "workspace" / "codevoyager.db"),
        )
    ).expanduser()
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None


@lru_cache
def get_settings() -> Settings:
    return Settings()
