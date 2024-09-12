# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install dependencies from the root requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set PYTHONPATH to include the app
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Command to be overwritten by docker-compose (either Celery worker or consumer)
CMD ["celery", "-A", "celery_app.celery_tasks", "worker", "--loglevel=info"]
