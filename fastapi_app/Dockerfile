# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install dependencies from the root requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Expose port for FastAPI
EXPOSE 8000

# Command to run FastAPI
CMD ["uvicorn", "fastapi_app.app:app", "--host", "0.0.0.0", "--port", "8000"]
