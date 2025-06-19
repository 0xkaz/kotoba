FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome dependencies
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install kotoba package in development mode
RUN pip install -e .

# Create non-root user
RUN useradd -m -s /bin/bash testuser && \
    chown -R testuser:testuser /app

# Install playwright browsers and set permissions
RUN playwright install chromium && \
    mkdir -p /home/testuser/.cache && \
    cp -r /root/.cache/ms-playwright /home/testuser/.cache/ && \
    chown -R testuser:testuser /home/testuser/.cache

USER testuser

# Set environment variable for Docker detection
ENV CONTAINER_ENV=docker

# Default command
CMD ["kotoba", "--help"]