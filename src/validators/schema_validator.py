"""Schema validation module using Pydantic."""

import logging
from typing import List, Optional

import pandas as pd
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class SurveyRecord(BaseModel):
    """Pydantic model for employee survey records."""
    employee_id: str
    department: str
    survey_date: str
    feedback_text: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5)

    @validator("employee_id")
    def validate_employee_id(cls, v: str) -> str:
        if not v.startswith("EMP-"):
            raise ValueError(f"Invalid employee_id format: {v}")
        return v


class SchemaValidator:
    """Validate DataFrame records against Pydantic schema."""

    def __init__(self) -> None:
        self.errors: List[dict] = []

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate each row and return only valid records."""
        valid_indices: List[int] = []
        self.errors = []

        required_cols = {"employee_id", "department", "survey_date", "feedback_text", "rating"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        for idx, row in df.iterrows():
            try:
                SurveyRecord(**row.to_dict())
                valid_indices.append(idx)
            except Exception as e:
                self.errors.append({"index": idx, "error": str(e)})

        if self.errors:
            logger.warning(f"Validation errors: {len(self.errors)} records rejected.")

        return df.loc[valid_indices].reset_index(drop=True)
