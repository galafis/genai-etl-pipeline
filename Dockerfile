FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY data/ ./data/
COPY .env.example ./.env

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

RUN python src/data/generate_synthetic_data.py

CMD ["python", "src/main.py"]
