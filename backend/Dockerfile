# Use an official Python image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Install missing networking utilities (fixes 'ip' command issue)
RUN apt-get update && apt-get install -y iproute2

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the app code
COPY . .

# Expose port 5000 for Flask
EXPOSE 5000

# Start the Flask server
CMD ["python", "server.py"]
