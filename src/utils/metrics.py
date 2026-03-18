"""Metricas e monitoramento do pipeline ETL."""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class PipelineMetrics:
    """Coleta e armazena metricas de execucao do pipeline."""

    records_extracted: int = 0
    records_transformed: int = 0
    records_enriched: int = 0
    records_loaded: int = 0
    records_failed: int = 0
    enrichment_success_rate: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    stage_durations: Dict[str, float] = field(default_factory=dict)
    _stage_start: Optional[float] = field(default=None, repr=False)
    _current_stage: Optional[str] = field(default=None, repr=False)

    def start_pipeline(self) -> None:
        """Marca o inicio da execucao do pipeline."""
        self.start_time = time.time()
        logger.info("Pipeline iniciado.")

    def end_pipeline(self) -> None:
        """Marca o fim da execucao do pipeline."""
        self.end_time = time.time()
        duration = self.end_time - (self.start_time or self.end_time)
        logger.info("Pipeline finalizado em %.2f segundos.", duration)

    def start_stage(self, stage_name: str) -> None:
        """Inicia a medicao de uma etapa do pipeline."""
        self._current_stage = stage_name
        self._stage_start = time.time()
        logger.info("Etapa '%s' iniciada.", stage_name)

    def end_stage(self) -> None:
        """Finaliza a medicao da etapa atual."""
        if self._current_stage and self._stage_start:
            duration = time.time() - self._stage_start
            self.stage_durations[self._current_stage] = duration
            logger.info(
                "Etapa '%s' concluida em %.2f segundos.",
                self._current_stage,
                duration,
            )
            self._current_stage = None
            self._stage_start = None

    @property
    def total_duration(self) -> float:
        """Retorna a duracao total do pipeline em segundos."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def calculate_success_rate(self) -> float:
        """Calcula a taxa de sucesso do enriquecimento."""
        total = self.records_enriched + self.records_failed
        if total > 0:
            self.enrichment_success_rate = self.records_enriched / total
        return self.enrichment_success_rate

    def summary(self) -> Dict[str, object]:
        """Retorna um resumo das metricas em formato de dicionario."""
        self.calculate_success_rate()
        return {
            "total_duration_seconds": round(self.total_duration, 2),
            "records_extracted": self.records_extracted,
            "records_transformed": self.records_transformed,
            "records_enriched": self.records_enriched,
            "records_loaded": self.records_loaded,
            "records_failed": self.records_failed,
            "enrichment_success_rate": round(
                self.enrichment_success_rate, 4
            ),
            "stage_durations": self.stage_durations,
        }
