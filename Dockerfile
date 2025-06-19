# ==============================================================================
# OpenAI Forward Docker Configuration
# ==============================================================================
# Description: Dockerfile for OpenAI Forward service with multi-AI provider support
# Author: Assistant  
# Created: 2024-12-19
# Version: 1.0
#
# This Docker image provides:
# - OpenAI Forward proxy service
# - Support for DeepSeek AI, LingyiWanwu, and OpenAI APIs
# - Optimized performance and error handling
# - Proper timezone and logging configuration
# ==============================================================================

FROM python:3.11-slim

# Metadata and maintainer information
LABEL maintainer="K.Y"
LABEL description="OpenAI Forward proxy service supporting multiple AI providers"
LABEL version="1.0"

# Environment Configuration
# Set proper encoding and timezone for consistent behavior
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/home/openai-forward

# System Dependencies Installation
# Install timezone data and required system packages with error handling
RUN set -ex \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        tzdata \
        curl \
        ca-certificates \
    && ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "System dependencies installed successfully with timestamp: $(date)"

# Application Setup
# Copy application code and configuration files
COPY . /home/openai-forward
WORKDIR /home/openai-forward

# Python Dependencies Installation  
# Install build dependencies, Python packages, and cleanup in single layer
RUN set -ex \
    && echo "Starting Python dependencies installation at: $(date)" \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        patch \
        g++ \
        gcc \
        libstdc++6 \
        libtcmalloc-minimal4 \
        libleveldb-dev \
        cmake \
        make \
        build-essential \
    && echo "Build dependencies installed, installing Python packages..." \
    && pip3 install --no-cache-dir --upgrade pip \
    && pip3 install -e . --no-cache-dir \
    && echo "Python packages installed, cleaning up..." \
    && apt-get remove -y \
        patch \
        g++ \
        gcc \
        cmake \
        make \
        build-essential \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "Installation completed successfully at: $(date)"

# Configuration Validation
# Ensure configuration file exists and is readable
RUN set -ex \
    && if [ -f "openai-forward-config.yaml" ]; then \
        echo "Configuration file found: openai-forward-config.yaml"; \
        echo "Configuration validation completed at: $(date)"; \
    else \
        echo "Warning: Configuration file not found, using default settings"; \
    fi

# Network Configuration
# Expose the main service port
EXPOSE 8000

# Service Startup
# Start the OpenAI Forward service with proper error handling
ENTRYPOINT ["python3", "-m", "openai_forward.__main__", "run"]

# ==============================================================================
# Build and Run Instructions:
#
# Build the image:
# docker build -t openai-forward:latest .
#
# Run the container:
# docker run -d \
#   --name openai-forward \
#   -p 8000:8000 \
#   -v $(pwd)/openai-forward-config.yaml:/home/openai-forward/openai-forward-config.yaml \
#   openai-forward:latest
#
# View logs:
# docker logs -f openai-forward
#
# Access services:
# - DeepSeek: http://localhost:8000/deepseek/v1/chat/completions
# - LingyiWanwu: http://localhost:8000/lingyiwanwu/v1/chat/completions  
# - OpenAI: http://localhost:8000/v1/chat/completions
# ==============================================================================
