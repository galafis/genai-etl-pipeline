# Data Directory

## Overview

This directory stores input/output data for the GenAI ETL pipeline. **No sensitive or real PII data is committed to this repository.**

## Data Dictionary

### Input Schema (Raw Text Documents)

| Column | Type | Description | Example |
|---|---|---|---|
| doc_id | STRING | Unique document identifier | doc_001 |
| source | STRING | Data source name | customer_feedback |
| raw_text | STRING | Unstructured text content | "Product quality is excellent..." |
| timestamp | DATETIME | Ingestion timestamp | 2026-01-15T10:30:00Z |
| metadata | JSON | Source-specific metadata | {"channel": "email"} |

### Output Schema (AI-Enriched)

| Column | Type | Description | Example |
|---|---|---|---|
| doc_id | STRING | Original document ID | doc_001 |
| sentiment | STRING | AI-classified sentiment | positive |
| entities | LIST[STRING] | Extracted named entities | ["Product X", "Brazil"] |
| summary | STRING | AI-generated summary | "Customer praises quality..." |
| categories | LIST[STRING] | Topic classifications | ["quality", "satisfaction"] |
| confidence | FLOAT | Model confidence score | 0.94 |

## Synthetic Data Generation

```bash
python -m src.generate_synthetic --rows 5000 --output data/sample_documents.parquet
```

## Public Data Sources Referenced

- **Brazilian Consumer Complaints (consumidor.gov.br)**: Public complaints dataset
- **Kaggle Customer Reviews**: Open-source product review datasets
- **IBGE Economic Surveys**: For demographic context enrichment
