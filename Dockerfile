FROM ubuntu:latest
LABEL authors="ouber"

ENTRYPOINT ["top", "-b"]
#Dockerfile to run django python application in a container
# Use the official Python image from the Docker Hub
# Use the official Python image from the Docker Hub
FROM python:3.9-slim
# Set the working directory in the container
WORKDIR /app
# Copy the requirements file into the container
COPY requirements.txt .
# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Copy the rest of the application code into the container
COPY . .
# Expose the port that the Django application will run on
EXPOSE 8000
# Run the Django application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# Use the official Ubuntu image from the Docker Hub
