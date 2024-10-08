from fastapi import FastAPI, HTTPException
import pika
import json
import threading
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# RabbitMQ Configuration from .env variables
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
EXCHANGE_NAME = os.getenv('EXCHANGE_NAME')
QUEUE_NAME = os.getenv('QUEUE_NAME')
ROUTING_KEY = os.getenv('ROUTING_KEY')

class RabbitMQ:
    def __init__(self, host: str):
        self.host = host
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct')
        self.channel.queue_declare(queue=QUEUE_NAME)
        self.channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=ROUTING_KEY)

    def publish_message(self, message: str):
        self.channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=message
        )
        print(f" [x] Sent {message}")

    def consume_message(self, callback):
        def callback_wrapper(ch, method, properties, body):
            callback(body.decode())

        self.channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback_wrapper, auto_ack=True)
        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

# Instantiate RabbitMQ
rabbitmq = RabbitMQ(RABBITMQ_HOST)

# Start consuming messages in a separate thread
def start_consumer():
    def handle_message(body):
        print(f" [x] Received {body}")
    
    rabbitmq.consume_message(handle_message)

consumer_thread = threading.Thread(target=start_consumer)
consumer_thread.start()

# In-memory data store for CRUD operations
items = {}

# CRUD Operations

@app.post("/items/")
async def create_item(item_id: str, item: dict):
    if item_id in items:
        raise HTTPException(status_code=400, detail="Item already exists")
    
    items[item_id] = item
    
    # Publish message to RabbitMQ when item is created
    message = json.dumps({"event": "item_created", "item_id": item_id, "item": item})
    rabbitmq.publish_message(message)
    
    return {"message": "Item created", "item": item}

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    item = items.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return item

@app.put("/items/{item_id}")
async def update_item(item_id: str, item: dict):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    
    items[item_id] = item
    
    # Publish message to RabbitMQ when item is updated
    message = json.dumps({"event": "item_updated", "item_id": item_id, "item": item})
    rabbitmq.publish_message(message)
    
    return {"message": "Item updated", "item": item}

@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    
    del items[item_id]
    
    # Publish message to RabbitMQ when item is deleted
    message = json.dumps({"event": "item_deleted", "item_id": item_id})
    rabbitmq.publish_message(message)
    
    return {"message": "Item deleted"}
