from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pika
import json
import threading
from dotenv import load_dotenv
import os
import time

# Load environment variables from .env file
load_dotenv()

# Create FastAPI app instance
app = FastAPI()

# RabbitMQ Configuration from .env variables
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
EXCHANGE_NAME = os.getenv('EXCHANGE_NAME')
QUEUE_NAME = os.getenv('QUEUE_NAME')
ROUTING_KEY = os.getenv('ROUTING_KEY')

class RabbitMQ:
    def __init__(self, host: str):
        self.host = host
        self.connection_publish = None
        self.channel_publish = None
        self.connection_consume = None
        self.channel_consume = None
        self.connect_publish()
        self.connect_consume()

    def connect_publish(self):
        """Establish a connection for publishing."""
        while True:
            try:
                self.connection_publish = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
                self.channel_publish = self.connection_publish.channel()
                self.channel_publish.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct')
                self.channel_publish.queue_declare(queue=QUEUE_NAME)
                self.channel_publish.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=ROUTING_KEY)
                print("RabbitMQ publish connection connected.")
                break
            except pika.exceptions.AMQPConnectionError:
                print("Failed to connect to RabbitMQ for publishing. Retrying in 5 seconds...")
                time.sleep(5)

    def connect_consume(self):
        """Establish a connection for consuming."""
        while True:
            try:
                self.connection_consume = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
                self.channel_consume = self.connection_consume.channel()
                self.channel_consume.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct')
                self.channel_consume.queue_declare(queue=QUEUE_NAME)
                self.channel_consume.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=ROUTING_KEY)
                print("RabbitMQ consume connection connected.")
                break
            except pika.exceptions.AMQPConnectionError:
                print("Failed to connect to RabbitMQ for consuming. Retrying in 5 seconds...")
                time.sleep(5)

    def publish_message(self, message: dict):
        """Publish a message to RabbitMQ with reconnection logic."""
        try:
            # Serialize the message to JSON and encode it as UTF-8 bytes
            message_body = json.dumps(message).encode('utf-8')
            self.channel_publish.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=ROUTING_KEY,
                body=message_body
            )
            print(f" [x] Sent {message}")
        except pika.exceptions.ChannelWrongStateError as e:
            print(f"Publish channel is closed. Reconnecting...: {e}")
            self.connect_publish()
            self.publish_message(message)  # Retry publishing after reconnection
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Publish connection error. Reconnecting...: {e}")
            self.connect_publish()
            self.publish_message(message)  # Retry publishing after reconnection

    def consume_message(self, callback):
        """Start consuming messages."""
        while True:
            try:
                self.channel_consume.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
                print(' [*] Waiting for messages. To exit press CTRL+C')
                self.channel_consume.start_consuming()
            except pika.exceptions.ChannelWrongStateError as e:
                print(f"Consume channel is closed. Reconnecting...: {e}")
                self.connect_consume()
            except pika.exceptions.AMQPConnectionError as e:
                print(f"Consume connection error. Reconnecting...: {e}")
                self.connect_consume()

# Instantiate RabbitMQ
rabbitmq = RabbitMQ(RABBITMQ_HOST)

# Start consuming messages in a separate thread
def start_consumer():
    def handle_message(ch, method, properties, body):
        try:
            message = body.decode('utf-8')
            print(f" [x] Received {message}")
        except Exception as e:
            print(f"Error decoding message: {e}")

    rabbitmq.consume_message(handle_message)

consumer_thread = threading.Thread(target=start_consumer, daemon=True)
consumer_thread.start()

# In-memory data store for CRUD operations
items = {}

# Pydantic model for request body validation
class ItemData(BaseModel):
    item_id: str
    item: dict

# CRUD Operations

@app.post("/items/")
async def create_item(item_data: ItemData):
    if item_data.item_id in items:
        raise HTTPException(status_code=400, detail="Item already exists")
    
    items[item_data.item_id] = item_data.item
    
    # Publish message to RabbitMQ when item is created
    message = {"event": "item_created", "item_id": item_data.item_id, "item": item_data.item}
    rabbitmq.publish_message(message)
    
    return {"message": "Item created", "item": item_data.item}

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
    message = {"event": "item_updated", "item_id": item_id, "item": item}
    rabbitmq.publish_message(message)
    
    return {"message": "Item updated", "item": item}

@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    
    del items[item_id]
    
    # Publish message to RabbitMQ when item is deleted
    message = {"event": "item_deleted", "item_id": item_id}
    rabbitmq.publish_message(message)
    
    return {"message": "Item deleted"}
