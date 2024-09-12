import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from celery_app.celery_tasks import process_event_task

# Trigger the task using Celery's delay method
result = process_event_task.delay({'request_id': 130, 'data': 'example data'})

# Optionally, wait for the task result
print("Task submitted.")
print(f"Task ID: {result.id}")

# You can wait for the result if needed
result_value = result.get(timeout=10)  # Will wait up to 10 seconds for the task to complete
print(f"Task result: {result_value}")
