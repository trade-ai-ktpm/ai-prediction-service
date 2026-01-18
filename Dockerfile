FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/    
COPY .env.example .env
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8002

CMD ["sh", "/app/start.sh"]
