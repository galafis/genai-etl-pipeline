"""GenAI ETL Pipeline - Main entry point.

Orchestrates the full ETL pipeline with GenAI-powered transformations.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd

from config import get_config, PipelineConfig
from extractors.csv_extractor import CSVExtractor
from validators.schema_validator import SchemaValidator
from transformers.genai_transformer import GenAITransformer
from transformers.data_enricher import DataEnricher
from loaders.csv_loader import CSVLoader
from loaders.parquet_loader import ParquetLoader
from loaders.sqlite_loader import SQLiteLoader
from utils.logger import setup_logger
from utils.metrics import PipelineMetrics


class GenAIETLPipeline:
    """Main ETL pipeline with GenAI-powered transformations.

    Orchestrates extraction, validation, transformation,
    enrichment, and loading of data with LLM capabilities.
    """

    def __init__(self, config: Optional[PipelineConfig] = None) -> None:
        self.config = config or get_config()
        self.logger = setup_logger(__name__, level=self.config.log_level)
        self.metrics = PipelineMetrics()

        # Initialize components
        self.extractor = CSVExtractor()
        self.validator = SchemaValidator()
        self.enricher = DataEnricher()

        # GenAI transformer (optional)
        self.genai_transformer: Optional[GenAITransformer] = None
        if self.config.enable_genai:
            try:
                self.config.openai.validate()
                self.genai_transformer = GenAITransformer(
                    api_key=self.config.openai.api_key,
                    model=self.config.openai.model,
                    max_tokens=self.config.openai.max_tokens,
                    temperature=self.config.openai.temperature,
                    max_retries=self.config.openai.max_retries,
                    batch_size=self.config.openai.batch_size,
                )
                self.logger.info("GenAI transformer initialized successfully.")
            except ValueError as e:
                self.logger.warning(
                    f"GenAI disabled: {e}. Running pipeline without AI enrichment."
                )

        # Initialize loaders
        self._init_loaders()

    def _init_loaders(self) -> None:
        """Initialize output loaders based on configuration."""
        self.loaders = {
            "csv": CSVLoader(),
            "parquet": ParquetLoader(),
            "sqlite": SQLiteLoader(db_path=str(self.config.sqlite_db_path)),
        }

    def extract(self) -> pd.DataFrame:
        """Extract data from source files."""
        self.logger.info(f"Extracting data from {self.config.input_path}")
        self.metrics.start_step("extract")

        df = self.extractor.extract(str(self.config.input_path))

        self.metrics.end_step("extract", records=len(df))
        self.logger.info(f"Extracted {len(df)} records.")
        return df

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate extracted data against schema."""
        self.logger.info("Validating data schema...")
        self.metrics.start_step("validate")

        df_valid = self.validator.validate(df)
        rejected = len(df) - len(df_valid)

        self.metrics.end_step("validate", records=len(df_valid))
        if rejected > 0:
            self.logger.warning(f"Rejected {rejected} invalid records.")
        self.logger.info(f"Validation passed: {len(df_valid)} valid records.")
        return df_valid

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply GenAI transformations to the data."""
        if self.genai_transformer is None:
            self.logger.info("Skipping GenAI transformation (disabled).")
            return df

        self.logger.info("Applying GenAI transformations...")
        self.metrics.start_step("transform")

        df = self.genai_transformer.transform(df, text_column="feedback_text")

        self.metrics.end_step("transform", records=len(df))
        self.logger.info("GenAI transformation completed.")
        return df

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived columns and aggregations."""
        self.logger.info("Enriching data with derived columns...")
        self.metrics.start_step("enrich")

        df = self.enricher.enrich(df)

        self.metrics.end_step("enrich", records=len(df))
        self.logger.info("Data enrichment completed.")
        return df

    def load(self, df: pd.DataFrame) -> None:
        """Load enriched data to configured outputs."""
        self.logger.info(f"Loading data (format: {self.config.output_format})...")
        self.metrics.start_step("load")

        output_path = str(self.config.output_path)
        loader = self.loaders.get(self.config.output_format)

        if loader is None:
            raise ValueError(f"Unsupported output format: {self.config.output_format}")

        loader.load(df, output_path)

        # Also save to SQLite for querying
        sqlite_loader = self.loaders["sqlite"]
        sqlite_loader.load(df, "enriched_surveys")

        self.metrics.end_step("load", records=len(df))
        self.logger.info(f"Data loaded successfully to {output_path}.")

    def run(self) -> pd.DataFrame:
        """Execute the full ETL pipeline."""
        self.logger.info("=" * 60)
        self.logger.info("Starting GenAI ETL Pipeline")
        self.logger.info("=" * 60)

        start_time = time.time()

        try:
            # ETL Steps
            df = self.extract()
            df = self.validate(df)
            df = self.transform(df)
            df = self.enrich(df)
            self.load(df)

            elapsed = time.time() - start_time
            self.logger.info(f"Pipeline completed in {elapsed:.2f}s")
            self.logger.info(f"Final record count: {len(df)}")
            self.metrics.log_summary(self.logger)

            return df

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise


def main() -> None:
    """Main entry point for the ETL pipeline."""
    config = get_config()
    pipeline = GenAIETLPipeline(config=config)
    pipeline.run()


if __name__ == "__main__":
    main()
