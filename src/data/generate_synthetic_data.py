"""Generate synthetic employee survey data.

Creates realistic synthetic data for pipeline testing.
No real personal data is used - all records are generated with Faker.
"""

import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

try:
    from faker import Faker
except ImportError:
    print("Faker not installed. Run: pip install faker")
    sys.exit(1)

fake_br = Faker("pt_BR")
Faker.seed(42)
random.seed(42)

NUM_RECORDS = 1000
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"

DEPARTMENTS = [
    "Engenharia", "Recursos Humanos", "Financeiro", "Marketing",
    "Vendas", "Operacoes", "TI", "Juridico", "Atendimento ao Cliente",
    "Logistica", "P&D", "Administrativo",
]

POSITIVE = [
    "Estou muito satisfeito com o ambiente de trabalho.",
    "O programa de beneficios e excelente.",
    "Meu gestor oferece feedback construtivo.",
    "Great leadership and clear communication.",
]

NEGATIVE = [
    "A comunicacao entre departamentos precisa melhorar.",
    "Nao ha oportunidades de crescimento.",
    "Carga de trabalho muito alta.",
    "Work-life balance is severely lacking.",
]

NEUTRAL = [
    "Ambiente adequado, mas poderia melhorar.",
    "Salario na media do mercado.",
    "Facilities are adequate for the work.",
]


def generate_feedback(sentiment: str) -> str:
    templates = {"positive": POSITIVE, "negative": NEGATIVE, "neutral": NEUTRAL}
    return random.choice(templates.get(sentiment, NEUTRAL))


def generate_records(n: int = NUM_RECORDS) -> List[Dict]:
    records = []
    start = datetime(2023, 1, 1)
    end = datetime(2025, 12, 31)
    for i in range(n):
        sentiment = random.choices(["positive", "negative", "neutral"], weights=[0.45, 0.30, 0.25], k=1)[0]
        rating_map = {"positive": random.randint(4, 5), "negative": random.randint(1, 2), "neutral": random.randint(2, 4)}
        date = start + timedelta(days=random.randint(0, (end - start).days))
        records.append({
            "employee_id": f"EMP-{i+1:05d}",
            "department": random.choice(DEPARTMENTS),
            "survey_date": date.strftime("%Y-%m-%d"),
            "feedback_text": generate_feedback(sentiment),
            "rating": rating_map[sentiment],
        })
    return records


def save_to_csv(records: List[Dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["employee_id", "department", "survey_date", "feedback_text", "rating"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    print(f"Generated {len(records)} records -> {path}")


def main() -> None:
    output = OUTPUT_DIR / "employee_surveys.csv"
    records = generate_records(NUM_RECORDS)
    save_to_csv(records, output)


if __name__ == "__main__":
    main()
