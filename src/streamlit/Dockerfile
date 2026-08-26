FROM python:3.12-slim

WORKDIR /app

COPY ./src/streamlit/requirements.txt .

RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

COPY ./src/streamlit/. .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
