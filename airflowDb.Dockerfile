FROM apache/airflow:2.9.2
RUN pip install --upgrade pip && pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" sqlmodel==0.0.10 python-dotenv==1.0.1
