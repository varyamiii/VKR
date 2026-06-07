from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ATC Speech Trainer"
    database_url: str = "postgresql://postgres:postgres@postgres:5432/vkr_atc_training"
    tts_service_url: str = "http://tts_service:8001"
    base_dir: Path = Path(__file__).resolve().parents[1]
    static_dir: Path = base_dir / "static"
    generated_audio_dir: Path = static_dir / "generated_audio"
    reports_dir: Path = static_dir / "reports"
    noises_dir: Path = static_dir / "noises"
    default_questions_count: int = 10
    default_speed: float = 1.0
    report_font_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.generated_audio_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    settings.noises_dir.mkdir(parents=True, exist_ok=True)
    return settings
