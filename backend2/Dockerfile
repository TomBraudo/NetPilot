# Use Python 3.10 slim image to match your local environment
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies including PostgreSQL development headers
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose port
EXPOSE 8080

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Run the application
CMD ["python", "server.py"]
