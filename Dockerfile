FROM python:3.11-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create workspace directory structure
RUN mkdir -p /workspace/raw /workspace/canonical /workspace/scripts /workspace/output /workspace/flagged

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WORKSPACE_DIR=/workspace

# Default command (can be overridden)
CMD ["python", "--version"]
