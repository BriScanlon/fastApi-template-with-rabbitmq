
# FastAPI & Database Subscriber with RabbitMQ and MongoDB

This project contains a FastAPI service and a separate `database_subscriber` service. Both services communicate through RabbitMQ, where the FastAPI service publishes messages, and the subscriber service listens for these messages, storing them in a MongoDB database.

## Project Structure

```bash
project-root/
│
├── fastapi/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
│
├── database_subscriber/
│   ├── Dockerfile
│   ├── db_subscriber.py
│   └── requirements.txt
│
└── docker-compose.yml
```

### Services

1. **FastAPI**: 
    - Provides an API to perform CRUD operations and publishes messages to RabbitMQ.
2. **Database Subscriber**: 
    - Listens to the RabbitMQ queue for messages and stores them in MongoDB.
3. **RabbitMQ**: 
    - Acts as the message broker between the FastAPI service and the subscriber.
4. **MongoDB**: 
    - Stores the messages received from RabbitMQ via the subscriber service.

---

## Requirements

To run the services locally, you will need:

- Docker
- Docker Compose

---

## Environment Variables

The project relies on an `.env` file for configuration. Ensure that the `.env` file is located at the root of the project. Example:

### Example `.env` file

```bash
# MongoDB Configuration
MONGO_DB_URL=mongodb://localhost:27017/
DATABASE_NAME=message_db
COLLECTION_NAME=message_logs

# RabbitMQ Configuration
RABBITMQ_HOST=rabbitmq
QUEUE_NAME=my_queue
```

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo-url.git
cd your-repo
```

### 2. Set Up the `.env` File

Create a `.env` file in the root of your project based on the provided template above.

### 3. Build and Start the Services

Build and run all the services using Docker Compose:

```bash
docker-compose up --build
```

This command will:

- Build and start the FastAPI service.
- Build and start the database subscriber.
- Spin up RabbitMQ with its default management interface at `http://localhost:15672` (default login: `guest` / `guest`).
- Start MongoDB at `mongodb://localhost:27017`.

### 4. Accessing the Services

- **FastAPI**: Once the services are up, you can access the FastAPI service at `http://localhost:8000`. The interactive API docs are available at:

    ```
    http://localhost:8000/docs
    ```

- **RabbitMQ**: The RabbitMQ Management interface is accessible at:

    ```
    http://localhost:15672 (username: guest, password: guest)
    ```

### 5. Example API Endpoints

- `POST /items/`: Creates an item and publishes a message to RabbitMQ.
- `GET /items/{item_id}`: Retrieves an item from the in-memory data store.
- `PUT /items/{item_id}`: Updates an item and publishes a message to RabbitMQ.
- `DELETE /items/{item_id}`: Deletes an item and publishes a message to RabbitMQ.

### 6. Storing Messages in MongoDB

The `database_subscriber` service consumes messages from RabbitMQ and stores them in MongoDB. You can verify the messages by accessing the MongoDB database:

1. Install a MongoDB client (e.g., MongoDB Compass) or use the `mongo` shell:

    ```bash
    docker exec -it mongodb mongo
    ```

2. Run the following commands to view the stored messages:

    ```bash
    use message_db
    db.message_logs.find().pretty()
    ```

---

## Stopping the Services

To stop the services, run:

```bash
docker-compose down
```

This will stop and remove all the containers.

---

## Additional Notes

- **Scaling the Subscriber**: You can scale the `database_subscriber` service independently by running more instances:

    ```bash
    docker-compose up --scale database_subscriber=3
    ```

- **Data Persistence**: MongoDB data is persisted in the Docker volume defined in the `docker-compose.yml`. You can inspect or delete the data volume if needed.

- **Testing**: Use tools like `Postman` or `cURL` to interact with the FastAPI endpoints and verify the RabbitMQ and MongoDB integration.

---

## License

[MIT License](./LICENSE)

---

## Copyright

&copy; Brian Scanlon 2024
