FROM python:3.12-slim

WORKDIR /app

# System deps for matplotlib
RUN apt-get update && \
    apt-get install -y --no-install-recommends libfreetype6-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "bot/main.py"]
