# Use the official Python image from the Docker Hub
FROM python:3.12-slim

RUN apt-get update && apt-get install python3-pip -y

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY --chmod=777 . .

# Install Python package
RUN python -m pip install -e .

EXPOSE 8000
EXPOSE 8501

# Specify the command to run on container start
CMD ["sh", "-c", "streamlit run src/green_light_ui/app.py --server.port=8501 --server.address=0.0.0.0 && uvicorn fastapi_app:app --host '0.0.0.0' --port 8000"]