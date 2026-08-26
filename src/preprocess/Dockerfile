FROM python:3.12-slim

WORKDIR /app

COPY src/preprocess/requirements.txt ./src/preprocess/
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r src/preprocess/requirements.txt

COPY src/ ./src/
COPY data/ ./data/

CMD ["python", "src/preprocess/preprocess.py"]