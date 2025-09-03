FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DATA_DIR=/app/data \
    DOCS_DIR=/app/data/docs \
    LLM_PROVIDER=openai \
    LLM_MODEL=gpt-5-mini \
    LX_MODEL_ID=openai:gpt-5-mini

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data/docs /app/data/extracts

EXPOSE 8000
CMD ["sh","-c","uvicorn server.main:app --host 0.0.0.0 --port ${PORT}"]
