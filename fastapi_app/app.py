import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
import pika
import json
import time

# Database models
Base = declarative_base()

class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(Text)
    status = Column(String, default="pending")
    result = Column(Text, nullable=True)

# FastAPI app with lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./test.db')
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

    # Enable WAL mode for SQLite
    with engine.connect() as connection:
        connection.connection.execute("PRAGMA journal_mode=WAL;")

    # Create a new session to delete all records at startup
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Delete all records from the requests table
        db.query(Request).delete()
        db.commit()
        print("All records deleted from the requests table.")
    except Exception as e:
        db.rollback()
        print(f"Failed to delete records: {e}")
    finally:
        db.close()

    yield  # This moves the control to the app routes
    
    print("FastAPI application is shutting down...")

# Initialize FastAPI with lifespan
app = FastAPI(lifespan=lifespan)

# Pydantic model for incoming requests
class RequestModel(BaseModel):
    data: str

def send_to_queue(event_data, request_id):
    rabbitmq_user = os.getenv('RABBITMQ_DEFAULT_USER', 'guest')
    rabbitmq_pass = os.getenv('RABBITMQ_DEFAULT_PASS', 'guest')
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = os.getenv('RABBITMQ_PORT', '5672')
    rabbitmq_queue = os.getenv('CELERY_QUEUE_NAME', 'event_queue')

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=int(rabbitmq_port), credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=rabbitmq_queue)

    message = {"request_id": request_id, "data": event_data}
    channel.basic_publish(exchange='', routing_key=rabbitmq_queue, body=json.dumps(message))
    connection.close()

@app.post("/process_event")
async def process_event(request: RequestModel, background_tasks: BackgroundTasks):
    # Create a new engine and session for this request
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./test.db')
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

    # Enable WAL mode
    with engine.connect() as connection:
        connection.connection.execute("PRAGMA journal_mode=WAL;")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Save the request in the database
        new_request = Request(data=request.data, status="queued")
        db.add(new_request)
        db.commit()
        db.refresh(new_request)

        # Send to queue in the background
        background_tasks.add_task(send_to_queue, request.data, new_request.id)
        time.sleep(5)  # Simulate processing time
        
        return {"request_id": new_request.id, "status": "queued"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process event: {str(e)}")
    finally:
        db.close()

@app.get("/status/{request_id}")
def get_status(request_id: int):
    # Create a new engine and session for this request
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./test.db')
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

    # Enable WAL mode
    with engine.connect() as connection:
        connection.connection.execute("PRAGMA journal_mode=WAL;")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        request_entry = db.query(Request).filter(Request.id == request_id).all()
        l = []
        for i in request_entry:
            l.append({"request_id": i.id, "status": i.status})
        # return all the entries
        if request_entry:
            return l
        return {"error": "Request not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch status: {str(e)}")
    finally:
        db.close()

@app.get("/result/{request_id}")
def get_result(request_id: int):
    # Create a new engine and session for this request
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./test.db')
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

    # Enable WAL mode
    with engine.connect() as connection:
        connection.connection.execute("PRAGMA journal_mode=WAL;")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        request_entry = db.query(Request).filter(Request.id == request_id).first()
        if request_entry:
            return {"request_id": request_id, "result": request_entry.result}
        return {"error": "Result not found or request still processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch result: {str(e)}")
    finally:
        db.close()
