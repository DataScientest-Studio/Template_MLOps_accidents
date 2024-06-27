FROM apache/airflow:2.9.2
RUN pip install --upgrade pip && pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" sqlmodel python-dotenv pandas
