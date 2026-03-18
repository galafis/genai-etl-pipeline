"""Testes unitarios para o pipeline ETL com IA Generativa."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.config import Settings
from src.extractors.csv_extractor import CSVExtractor
from src.transformers.genai_transformer import GenAITransformer
from src.validators.schema_validator import SchemaValidator
from src.utils.metrics import PipelineMetrics


# --------------- Fixtures ---------------

@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Cria um DataFrame de exemplo para testes."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "nome": [
            "Ana Silva", "Carlos Souza", "Maria Oliveira",
            "Pedro Santos", "Lucia Costa",
        ],
        "departamento": [
            "Engenharia", "Marketing", "RH",
            "Financeiro", "Engenharia",
        ],
        "salario": [8500.0, 6200.0, 7100.0, 9300.0, 8800.0],
        "avaliacao": [4.5, 3.8, 4.2, 4.7, 4.1],
    })


@pytest.fixture
def temp_csv(sample_dataframe: pd.DataFrame) -> str:
    """Cria um arquivo CSV temporario para testes."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as f:
        sample_dataframe.to_csv(f, index=False)
        return f.name


@pytest.fixture
def mock_settings() -> Settings:
    """Cria configuracoes mockadas para testes."""
    settings = MagicMock(spec=Settings)
    settings.openai_api_key = "test-key-fake"
    settings.openai_model = "gpt-3.5-turbo"
    settings.max_tokens = 500
    settings.input_path = "data/input"
    settings.output_path = "data/output"
    return settings


# --------------- Testes do Extractor ---------------

class TestCSVExtractor:
    """Testes para o extrator de CSV."""

    def test_extract_valid_csv(
        self, temp_csv: str, mock_settings: Settings
    ) -> None:
        """Testa a extracao de um arquivo CSV valido."""
        extractor = CSVExtractor(file_path=temp_csv)
        df = extractor.extract()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert "nome" in df.columns

    def test_extract_file_not_found(
        self, mock_settings: Settings
    ) -> None:
        """Testa erro ao tentar extrair arquivo inexistente."""
        extractor = CSVExtractor(file_path="arquivo_inexistente.csv")
        with pytest.raises(FileNotFoundError):
            extractor.extract()


# --------------- Testes do Transformer ---------------

class TestGenAITransformer:
    """Testes para o transformador com IA Generativa."""

    def test_normalize_columns(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Testa a normalizacao de nomes de colunas."""
        df = sample_dataframe.copy()
        df.columns = ["ID", "Nome Completo", "Dept", "Salario", "Nota"]
        transformer = GenAITransformer()
        result = transformer.normalize_columns(df)
        assert all(
            col == col.lower().replace(" ", "_")
            for col in result.columns
        )

    def test_remove_duplicates(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Testa a remocao de duplicatas."""
        df = pd.concat(
            [sample_dataframe, sample_dataframe.iloc[:2]],
            ignore_index=True,
        )
        transformer = GenAITransformer()
        result = transformer.remove_duplicates(df)
        assert len(result) == 5

    def test_handle_missing_values(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Testa o tratamento de valores ausentes."""
        df = sample_dataframe.copy()
        df.loc[0, "salario"] = None
        transformer = GenAITransformer()
        result = transformer.handle_missing_values(
            df, strategy="mean", columns=["salario"]
        )
        assert result["salario"].isna().sum() == 0


# --------------- Testes do Validator ---------------

class TestSchemaValidator:
    """Testes para o validador de schema."""

    def test_validate_required_columns(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Testa a validacao de colunas obrigatorias."""
        required = ["id", "nome", "departamento"]
        validator = SchemaValidator(required_columns=required)
        assert validator.validate(sample_dataframe) is True

    def test_validate_missing_columns(
        self, sample_dataframe: pd.DataFrame
    ) -> None:
        """Testa a falha quando colunas obrigatorias estao ausentes."""
        required = ["id", "nome", "coluna_inexistente"]
        validator = SchemaValidator(required_columns=required)
        assert validator.validate(sample_dataframe) is False


# --------------- Testes das Metricas ---------------

class TestPipelineMetrics:
    """Testes para as metricas do pipeline."""

    def test_pipeline_duration(self) -> None:
        """Testa o calculo de duracao do pipeline."""
        metrics = PipelineMetrics()
        metrics.start_pipeline()
        metrics.end_pipeline()
        assert metrics.total_duration >= 0

    def test_success_rate_calculation(self) -> None:
        """Testa o calculo da taxa de sucesso."""
        metrics = PipelineMetrics()
        metrics.records_enriched = 90
        metrics.records_failed = 10
        rate = metrics.calculate_success_rate()
        assert rate == 0.9

    def test_summary_output(self) -> None:
        """Testa o formato do resumo de metricas."""
        metrics = PipelineMetrics()
        metrics.records_extracted = 100
        metrics.records_transformed = 95
        summary = metrics.summary()
        assert "records_extracted" in summary
        assert summary["records_extracted"] == 100


# --------------- Testes de Integracao ---------------

class TestPipelineIntegration:
    """Testes de integracao do pipeline."""

    def test_extract_and_transform(
        self, temp_csv: str
    ) -> None:
        """Testa o fluxo de extracao seguido de transformacao."""
        extractor = CSVExtractor(file_path=temp_csv)
        df = extractor.extract()
        transformer = GenAITransformer()
        result = transformer.normalize_columns(df)
        assert len(result) == 5
        assert all(
            col == col.lower().replace(" ", "_")
            for col in result.columns
        )

    def test_full_pipeline_without_api(
        self, temp_csv: str
    ) -> None:
        """Testa o pipeline completo sem chamadas a API."""
        extractor = CSVExtractor(file_path=temp_csv)
        df = extractor.extract()

        transformer = GenAITransformer()
        df = transformer.normalize_columns(df)
        df = transformer.remove_duplicates(df)

        required = ["id", "nome", "departamento"]
        validator = SchemaValidator(required_columns=required)
        assert validator.validate(df) is True

        metrics = PipelineMetrics()
        metrics.records_extracted = len(df)
        metrics.records_transformed = len(df)
        assert metrics.records_extracted == 5
