"""Parquet data loader module."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class ParquetLoader:
    """Load DataFrames to Parquet format."""

    def load(self, df: pd.DataFrame, output_path: str) -> None:
        """Write DataFrame to Parquet file."""
        path = Path(output_path)
        if not path.suffix:
            path = path.with_suffix(".parquet")
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(str(path), index=False, engine="pyarrow")
        logger.info(f"Saved {len(df)} records to {path}")


class CSVLoader:
    """Load DataFrames to CSV format."""

    def load(self, df: pd.DataFrame, output_path: str) -> None:
        path = Path(output_path)
        if not path.suffix:
            path = path.with_suffix(".csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(str(path), index=False, encoding="utf-8")
        logger.info(f"Saved {len(df)} records to {path}")


class SQLiteLoader:
    """Load DataFrames to SQLite database."""

    def __init__(self, db_path: str = "data/output/pipeline.db") -> None:
        self.db_path = db_path

    def load(self, df: pd.DataFrame, table_name: str) -> None:
        from sqlalchemy import create_engine
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(f"sqlite:///{self.db_path}")
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        logger.info(f"Loaded {len(df)} records to SQLite table '{table_name}'")
