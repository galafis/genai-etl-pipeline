"""Modulo de enriquecimento de dados com IA Generativa.

Utiliza a API da OpenAI para enriquecer registros com
informacoes contextuais, categorizacao e sentimento.
"""

import logging
from typing import Any, Dict, List, Optional

import openai
import pandas as pd

from src.config import Settings

logger = logging.getLogger(__name__)


class DataEnricher:
    """Enriquecedor de dados baseado em IA Generativa."""

    def __init__(self, settings: Settings) -> None:
        """Inicializa o enriquecedor com as configuracoes."""
        self.settings = settings
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.max_tokens
        logger.info("DataEnricher inicializado com modelo %s", self.model)

    def enrich_record(
        self, record: Dict[str, Any], prompt_template: str
    ) -> Dict[str, Any]:
        """Enriquece um unico registro utilizando a API da OpenAI."""
        try:
            prompt = prompt_template.format(**record)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Voce e um assistente especializado em "
                            "enriquecimento e categorizacao de dados."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=0.3,
            )
            enriched_text = response.choices[0].message.content.strip()
            record["ai_enrichment"] = enriched_text
            record["enrichment_model"] = self.model
            record["enrichment_status"] = "success"
            logger.debug("Registro enriquecido com sucesso.")
        except openai.APIError as e:
            logger.error("Erro na API da OpenAI: %s", str(e))
            record["ai_enrichment"] = None
            record["enrichment_status"] = "error"
        return record

    def enrich_dataframe(
        self,
        df: pd.DataFrame,
        prompt_template: str,
        batch_size: int = 10,
    ) -> pd.DataFrame:
        """Enriquece um DataFrame completo em lotes."""
        enriched_records: List[Dict[str, Any]] = []
        total = len(df)
        logger.info("Iniciando enriquecimento de %d registros.", total)

        for idx, row in df.iterrows():
            record = row.to_dict()
            enriched = self.enrich_record(record, prompt_template)
            enriched_records.append(enriched)

            if (idx + 1) % batch_size == 0:
                logger.info(
                    "Progresso: %d/%d registros processados.",
                    idx + 1,
                    total,
                )

        logger.info("Enriquecimento concluido: %d registros.", total)
        return pd.DataFrame(enriched_records)

    def classify_sentiment(
        self, text: str
    ) -> Optional[str]:
        """Classifica o sentimento de um texto."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Classifique o sentimento do texto como: "
                            "positivo, negativo ou neutro. "
                            "Responda apenas com a classificacao."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                max_tokens=10,
                temperature=0.0,
            )
            return response.choices[0].message.content.strip().lower()
        except openai.APIError as e:
            logger.error("Erro na classificacao de sentimento: %s", str(e))
            return None
