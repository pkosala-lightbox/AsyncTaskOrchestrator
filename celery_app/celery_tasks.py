import os
import sys
import time
import logging
import sqlite3
from celery import Celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from fastapi_app.app import Request  # Import the Request model from your FastAPI app

# Setup logging for the app
logging.basicConfig(level=logging.INFO)

# Fetch environment variables for Celery broker and SQLite database
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'pyamqp://guest@localhost//')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./test.db')

# Celery configuration
app = Celery('tasks', broker=CELERY_BROKER_URL)

@app.task
def process_event_task(data):
    # Simulate processing time
    time.sleep(5)

    # Extract request_id and event data from the message
    request_id = int(data['request_id'])
    event_data = data['data']

    logging.info(f"Processing data for request_id: {request_id}")

    # Create a new database engine and session for each task
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

    # Enable WAL mode to improve concurrency
    with engine.connect() as connection:
        connection.connection.execute("PRAGMA journal_mode=WAL;")

    # Session management
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    retries = 3
    while retries > 0:
        try:
            # Query the request from the database
            request_entry = db.query(Request).filter(Request.id == request_id).first()
            logging.info(f"Request entry: {request_entry} in database: {DATABASE_URL}.")

            if request_entry:
                # Update the request status to "processing"
                request_entry.status = "processing"
                db.add(request_entry)
                db.flush()  # Ensure the changes are flushed to the DB
                db.commit()  # Commit to save the status as "processing"
                logging.info(f"Updated request {request_entry.id} to status 'processing'.")

                # Simulate the result creation (this can be replaced with actual logic)
                result = f"Processed event: {event_data}"
                time.sleep(5)

                # Update the request with the result and mark it as "completed"
                request_entry.result = result
                request_entry.status = "completed"
                db.add(request_entry)
                db.flush()  # Ensure the result is flushed
                db.commit()  # Commit to save the final result
                db.refresh(request_entry)  # Refresh to ensure the session is up-to-date
                logging.info(f"Updated request {request_entry.id} to status 'completed'.")
                time.sleep(5)

                logging.info(f"Request {request_id} processing completed.")
                break
            else:
                logging.error(f"Request ID {request_id} not found in database.")
                break
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                retries -= 1
                time.sleep(1)  # Sleep for a second before retrying
                logging.error(f"Database is locked, retrying... {retries} retries left.")
            else:
                raise
        finally:
            db.close()  # Ensure the session is closed
