FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for sentence-transformers and FAISS
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy app code
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
