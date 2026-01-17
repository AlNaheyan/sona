FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application code first (needed for pyproject.toml install)
COPY pyproject.toml .
COPY backend/ ./backend/
COPY ml/ ./ml/

# Install Python dependencies (including dev for testing)
RUN pip install --no-cache-dir -e ".[dev]"

# Set Python path
ENV PYTHONPATH=/app

# Run the application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
