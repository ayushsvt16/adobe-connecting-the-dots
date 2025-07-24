# Use explicit AMD64 platform for compatibility
FROM --platform=linux/amd64 python:3.10-slim

# Set environment variables for better performance
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements_minimal.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements_minimal.txt

# Copy application code
COPY extractor_optimized.py .
COPY run_docker.py .

# Make run_docker.py executable
RUN chmod +x run_docker.py

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Set the entry point
CMD ["python", "run_docker.py"]
