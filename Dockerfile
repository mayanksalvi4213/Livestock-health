# Dockerfile
FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffering issues
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential gcc curl \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (cache layer)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Create a non-root user for safety
RUN useradd -m appuser
USER appuser

# Copy app code (dataset is ignored by .dockerignore)
COPY --chown=appuser:appuser . /app

# Expose port your Flask app uses
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
