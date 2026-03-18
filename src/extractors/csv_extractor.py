"""CSV data extractor module.

Handles extraction of data from CSV files with configurable options.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class CSVExtractor:
    """Extract data from CSV files.

    Supports configurable encoding, delimiter, and column selection.
    """

    def __init__(
        self,
        encoding: str = "utf-8",
        delimiter: str = ",",
        columns: Optional[List[str]] = None,
    ) -> None:
        self.encoding = encoding
        self.delimiter = delimiter
        self.columns = columns

    def extract(self, file_path: str) -> pd.DataFrame:
        """Extract data from a CSV file.

        Args:
            file_path: Path to the CSV file.

        Returns:
            DataFrame with extracted data.

        Raises:
            FileNotFoundError: If the file does not exist.
            pd.errors.EmptyDataError: If the file is empty.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        logger.info(f"Reading CSV from {file_path}")

        df = pd.read_csv(
            file_path,
            encoding=self.encoding,
            delimiter=self.delimiter,
            usecols=self.columns,
        )

        logger.info(f"Extracted {len(df)} rows, {len(df.columns)} columns.")
        return df

    def extract_multiple(self, file_paths: List[str]) -> pd.DataFrame:
        """Extract and concatenate data from multiple CSV files.

        Args:
            file_paths: List of paths to CSV files.

        Returns:
            Concatenated DataFrame.
        """
        frames: List[pd.DataFrame] = []

        for fp in file_paths:
            try:
                df = self.extract(fp)
                frames.append(df)
            except (FileNotFoundError, pd.errors.EmptyDataError) as e:
                logger.warning(f"Skipping {fp}: {e}")

        if not frames:
            return pd.DataFrame()

        return pd.concat(frames, ignore_index=True)
