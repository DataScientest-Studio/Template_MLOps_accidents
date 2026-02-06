# Streamlit Dashboard - Control Center UI
# Build from repo root: docker build -f services/dashboard/Dockerfile .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY services/dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/dashboard/.streamlit /app/.streamlit
COPY services/dashboard/app /app/app

EXPOSE 8501

CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
