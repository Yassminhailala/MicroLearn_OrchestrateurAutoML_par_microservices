FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    default-jdk-headless \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Verify Java is available (required for TorchServe)
RUN java -version

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy source code and config
COPY . .

# Create directory for model store and temp files
RUN mkdir -p models_temp model_store

# Make start script executable
RUN chmod +x start.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV TORCHSERVE_ENABLED=true

# Expose ports: 8080 (Flask), 8081 (TorchServe Inference), 8082 (TorchServe Management)
EXPOSE 8080 8081 8082

CMD ["./start.sh"]
