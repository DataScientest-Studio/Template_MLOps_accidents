# 
FROM python:3.8.10

# 
WORKDIR /api

# 
# COPY requirements.txt .
COPY . .

# 
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Expose the port on which the application will run
EXPOSE 8000

# 
CMD ["uvicorn", "app:app","--host", "0.0.0.0","--port","8000"]