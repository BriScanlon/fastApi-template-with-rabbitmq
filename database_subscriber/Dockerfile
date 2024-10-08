# Database Subscriber Dockerfile

# Use the official Python image
FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the database subscriber
CMD ["python", "db_subscriber.py"]
