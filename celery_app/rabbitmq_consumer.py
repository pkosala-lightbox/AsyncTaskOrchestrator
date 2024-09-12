import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import pika
import logging
import json
from celery_app.celery_tasks import process_event_task

logging.basicConfig(level=logging.INFO)

# Fetch RabbitMQ configuration from environment variables
RABBITMQ_USER = os.getenv('RABBITMQ_DEFAULT_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_DEFAULT_PASS', 'guest')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')  # Use 'rabbitmq' service name
RABBITMQ_PORT = os.getenv('RABBITMQ_PORT', '5672')
RABBITMQ_QUEUE = os.getenv('CELERY_QUEUE_NAME', 'event_queue')

def consume_queue():
    """
    Consumes messages from RabbitMQ and triggers the Celery task to process each message.
    """
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection_params = pika.ConnectionParameters(host=RABBITMQ_HOST, port=int(RABBITMQ_PORT), credentials=credentials)

    # Retry mechanism to wait for RabbitMQ to be available
    for attempt in range(5):
        try:
            logging.info(f"Attempt {attempt + 1}: Connecting to RabbitMQ...")
            connection = pika.BlockingConnection(connection_params)
            channel = connection.channel()
            break
        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"Connection attempt {attempt + 1} failed: {e}")
            time.sleep(5)  # Wait for 5 seconds before retrying
    else:
        logging.error("Failed to connect to RabbitMQ after 5 attempts. Exiting.")
        return

    # Declare the queue in case it doesn't exist yet
    channel.queue_declare(queue=RABBITMQ_QUEUE)

    # Callback to process the message
    def callback(ch, method, properties, body):
        try:
            data = json.loads(body.decode('utf-8'))
            process_event_task.delay(data)  # Trigger the Celery task
            logging.info(f"Received and processed message: {data}")
        except json.JSONDecodeError:
            logging.error(f"Error decoding message: {body}")

    # Correct for pika==0.13, using 'callback' argument instead of 'on_message_callback'
    channel.basic_consume(callback, queue=RABBITMQ_QUEUE, no_ack=True)
    logging.info("Waiting for messages...")
    channel.start_consuming()

if __name__ == "__main__":
    consume_queue()
