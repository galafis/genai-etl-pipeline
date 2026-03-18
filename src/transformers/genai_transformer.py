"""GenAI Transformer module.

Applies LLM-powered transformations to text data using OpenAI API.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import pandas as pd
from openai import OpenAI

logger = logging.getLogger(__name__)


class GenAITransformer:
    """Transform text data using OpenAI GPT models."""

    SENTIMENT_PROMPT = """Analyze the sentiment of the following employee feedback.
Return a JSON object with:
- "sentiment": one of "positive", "negative", "neutral", "mixed"
- "score": confidence score from 0.0 to 1.0
- "topics": list of up to 3 main topics
- "summary": one-sentence summary in the same language

Text: {text}

Respond ONLY with valid JSON."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 500,
        temperature: float = 0.3,
        max_retries: int = 3,
        batch_size: int = 10,
    ) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_retries = max_retries
        self.batch_size = batch_size
        self._api_calls = 0
        self._total_tokens = 0

    def _call_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Make a single API call with retry logic."""
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a data analysis assistant. Always respond with valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                self._api_calls += 1
                if response.usage:
                    self._total_tokens += response.usage.total_tokens
                content = response.choices[0].message.content
                if content:
                    return json.loads(content.strip())
                return None
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON on attempt {attempt + 1}")
            except Exception as e:
                wait_time = 2 ** attempt
                logger.warning(f"API error attempt {attempt + 1}: {e}. Retry in {wait_time}s")
                time.sleep(wait_time)
        logger.error("Max retries exceeded.")
        return None

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of a single text."""
        if not text or not text.strip():
            return {"sentiment": "neutral", "score": 0.5, "topics": [], "summary": ""}
        prompt = self.SENTIMENT_PROMPT.format(text=text[:2000])
        result = self._call_api(prompt)
        if result is None:
            return {"sentiment": "unknown", "score": 0.0, "topics": [], "summary": "Analysis failed."}
        return {
            "sentiment": result.get("sentiment", "unknown"),
            "score": float(result.get("score", 0.0)),
            "topics": result.get("topics", []),
            "summary": result.get("summary", ""),
        }

    def transform(self, df: pd.DataFrame, text_column: str = "feedback_text") -> pd.DataFrame:
        """Apply GenAI transformations to a DataFrame."""
        if text_column not in df.columns:
            logger.warning(f"Column '{text_column}' not found. Skipping.")
            return df
        logger.info(f"Processing {len(df)} records...")
        results = [self.analyze_sentiment(str(row[text_column])) for _, row in df.iterrows()]
        df = df.copy()
        df["sentiment"] = [r["sentiment"] for r in results]
        df["sentiment_score"] = [r["score"] for r in results]
        df["topics"] = [json.dumps(r["topics"]) for r in results]
        df["summary"] = [r["summary"] for r in results]
        logger.info(f"Done. API calls: {self._api_calls}, Tokens: {self._total_tokens}")
        return df

    @property
    def stats(self) -> Dict[str, int]:
        """Return API usage statistics."""
        return {"api_calls": self._api_calls, "total_tokens": self._total_tokens}
