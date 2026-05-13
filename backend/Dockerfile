FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .

COPY . .

# Entrypoint script'i çalıştırılabilir yap (Windows'ta git checkout yapan için)
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
# Default CMD: entrypoint (alembic + seed + uvicorn). compose dosyası da bu komutu kullanır.
CMD ["/app/entrypoint.sh"]
