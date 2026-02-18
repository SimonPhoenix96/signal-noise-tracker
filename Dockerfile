FROM python:3.11-slim

LABEL maintainer="jd@openclaw.ai"
LABEL description="Cronjob Money-MVP - RSS Feed Agent Orchestrator"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for database
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Berlin

# Non-root user for security
RUN useradd -m -u 1000 cronjob && \
    chown -R cronjob:cronjob /app

USER cronjob

# Default command
CMD ["python3", "main.py", "--start"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sqlite3; conn = sqlite3.connect('/app/data/cronjob.db'); conn.close()" || exit 1
