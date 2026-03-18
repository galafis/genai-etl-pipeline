"""Pipeline configuration module.

Loads environment variables and defines pipeline settings.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
OUTPUT_DIR: Path = DATA_DIR / "output"
LOGS_DIR: Path = BASE_DIR / "logs"


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI API integration."""

    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))
    max_tokens: int = 500
    temperature: float = 0.3
    max_retries: int = 3
    retry_delay: float = 1.0
    batch_size: int = 10
    timeout: int = 30

    def validate(self) -> None:
        """Validate that required configuration is present."""
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not set. Copy .env.example to .env and add your key."
            )


@dataclass
class PipelineConfig:
    """Main pipeline configuration."""

    input_path: Path = field(default_factory=lambda: DATA_DIR / "raw" / "employee_surveys.csv")
    output_format: str = "parquet"
    output_path: Path = field(default_factory=lambda: OUTPUT_DIR / "enriched_surveys")
    sqlite_db_path: Path = field(default_factory=lambda: OUTPUT_DIR / "pipeline.db")
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    enable_genai: bool = True
    enable_cache: bool = True
    cache_ttl_hours: int = 24

    openai: OpenAIConfig = field(default_factory=OpenAIConfig)

    def __post_init__(self) -> None:
        """Create necessary directories after initialization."""
        for directory in [DATA_DIR, OUTPUT_DIR, LOGS_DIR, DATA_DIR / "raw"]:
            directory.mkdir(parents=True, exist_ok=True)


def get_config() -> PipelineConfig:
    """Factory function to create pipeline configuration."""
    return PipelineConfig()
