import pika
import json
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# MongoDB Configuration from .env variables
MONGO_DB_URL = os.getenv('MONGO_DB_URL')
DATABASE_NAME = os.getenv('DATABASE_NAME')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')

# Connect to MongoDB
client = MongoClient(MONGO_DB_URL)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# RabbitMQ Configuration from .env variables
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
QUEUE_NAME = os.getenv('QUEUE_NAME')

# Function to handle incoming RabbitMQ messages
def callback(ch, method, properties, body):
    message = body.decode()
    data = json.loads(message)
    print(f" [x] Received {message}")

    # Store the message in the MongoDB collection
    collection.insert_one({
        "event": data['event'],
        "message": message
    })
    print(f" [x] Stored message in MongoDB")

# Setup RabbitMQ connection and consumer
def consume_messages():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    
    channel.queue_declare(queue=QUEUE_NAME)

    channel.basic_consume(
        queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True
    )
    
    print(f' [*] Waiting for messages in queue: {QUEUE_NAME}. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == "__main__":
    consume_messages()
