FROM python:3.9-slim

WORKDIR /app

COPY src/train/requirements.txt ./src/train/
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r src/train/requirements.txt

COPY src/ ./src/
COPY data/ ./data/

CMD ["python", "src/train/train_model.py"]