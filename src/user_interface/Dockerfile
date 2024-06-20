

# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Specify the command to run on container start

EXPOSE 8000
EXPOSE 8501

# CMD bash 


#CMD ["streamlit", "run", "app.py"]
# CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
CMD ["sh", "-c", "uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 & streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]