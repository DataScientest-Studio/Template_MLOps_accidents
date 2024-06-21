FROM python:3.9-slim

RUN apt-get update && apt-get install python3-pip -y

#set up a Working directory in the container
WORKDIR /app

#copy in the needed requirements and files
COPY requirements.txt .
COPY . .

#installing all necessary requirements
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

#run the application
CMD ["python", "src/models/api.py"]