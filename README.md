

# FastAPI + Celery + RabbitMQ Async Event Processing

This project demonstrates how to build an asynchronous task processing system using FastAPI, Celery, RabbitMQ, and SQLite in Docker. The system allows clients to submit requests, store them in a queue, process them asynchronously using Celery workers, and fetch results.

## Features:
- **FastAPI** for handling client requests.
- **RabbitMQ** for message queuing.
- **Celery** for distributed task processing.
- **SQLite** for lightweight local database storage.
- **Docker** to containerize the entire setup.
  
## Setup Instructions

### 1. Running Locally with Docker Compose
To run the entire setup locally:
1. Navigate to the root folder.
2. Run the following command to start all the services using single docker command:
   ```
   docker-compose up --build
   ```
3. To stop all the services and delete docker images, click Ctrl+C and run following command:
   ```
   docker-compose down
   ```

### 2. Running Locally without Docker
Steps to run the FastAPI app and Celery tasks locally for development or testing without Docker.

#### Requirements:
- Python 3.9+
- RabbitMQ installed locally

#### Steps:
1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   <!-- source venv/bin/activate - linux -->
   .\venv\Scripts\activate
   ```
2. Install the requirements:
   ```bash
   pip install -r fastapi_app/requirements.txt
   pip install -r celery_app/requirements.txt
   ```
3. Run the FastAPI app locally using either of the commands:
   ```
   uvicorn fastapi_app.app:app --reload
   python -m uvicorn fastapi_app.app:app --reload
   ```
4. Start Celery worker:
   
   1. To start the worker: 
   ```
   python -m celery -A celery_app.celery_tasks worker --loglevel=info --pool=solo
   ```
   2. To Open Flower Dashboard: 
   ```
   python -m celery -A celery_app.celery_tasks flower --port=5555
   ```
   3. To view the registered Tasks (for troubleshooting)
   ```
   python -m celery -A celery_app.celery_tasks inspect registered
   ```
5. Start Consumer:
   If Celery is natively integrated with RabbitMQ it directly handle task queues without needing custom consumers. Use following command to start the consumer:
   ```
   python rabbitmq_consumer.py
   ```

### 3. Testing and Running Functions Locally
You can run individual functions or test cases using `pytest`.

1. Install `pytest`:
   ```bash
   pip install pytest
   ```

2. Run the tests:
   ```bash
   pytest tests/
   ```

## Test Cases
Test cases are available in the `tests/` folder for local testing.

## Ideal Project Structure
```bash
.
├── fastapi_app/
│   ├── app.py                # FastAPI main app
│   ├── Dockerfile            # Dockerfile for FastAPI
│   ├── requirements.txt      # Dependencies for FastAPI
│
├── celery_app/
│   ├── celery_tasks.py       # Celery worker tasks
│   ├── Dockerfile            # Dockerfile for Celery worker
│   ├── requirements.txt      # Dependencies for Celery
│
├── tests/
│   ├── test_app.py           # Test cases for FastAPI app
│
├── docker-compose.yml        # Docker Compose to orchestrate services
└── README.md                 # Documentation
```

## APIs
- `POST /process_event`: Submit a new event to be processed.
- `GET /status/{request_id}`: Check the status of a request.
- `GET /result/{request_id}`: Fetch the result of a processed request.
