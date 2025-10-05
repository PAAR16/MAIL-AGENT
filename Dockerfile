# Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's layer caching
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 5001

# Define the command to run the application using Gunicorn
# It will run the 'app' object from the 'app.py' file.
# We bind to 0.0.0.0 to make it accessible from outside the container.
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5001", "app:app"]