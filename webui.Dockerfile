# ==============================================================================
# OpenAI Forward WebUI Docker Container Configuration
# ==============================================================================
# Description: Dockerfile for building OpenAI Forward with integrated WebUI
# Author: kunyuan
# Created: 2024-12-19
# Updated: 2024-12-19
# Version: 2.0
#
# Features:
# - Streamlit-based WebUI for configuration management
# - Real-time configuration updates via ZeroMQ
# - Multi-port exposure for API and WebUI
# - Built-in health checks and monitoring
# - Timezone configuration for proper logging
# ==============================================================================

# Use Python 3.10 slim base image for smaller footprint
FROM python:3.10-slim

# Metadata and maintainer information
LABEL maintainer="kunyuan"
LABEL description="OpenAI Forward with WebUI - Advanced API Proxy with Web Interface"
LABEL version="2.0"

# Environment configuration for proper UTF-8 encoding and timezone
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV DEBIAN_FRONTEND=noninteractive

# Configure timezone for proper log timestamps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tzdata \
        curl \
        wget && \
    ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create application directory and copy source code
COPY . /home/openai-forward

# Set working directory
WORKDIR /home/openai-forward

# Install build dependencies and Python packages
# Note: Using multi-stage approach to reduce final image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        patch \
        g++ \
        gcc \
        libstdc++6 \
        libtcmalloc-minimal4 \
        libleveldb-dev \
        cmake \
        make \
        build-essential && \
    # Install Python dependencies with WebUI support
    pip3 install --no-cache-dir \
        -e .[webui] && \
    # Clean up build dependencies to reduce image size
    apt-get remove -y \
        patch \
        g++ \
        gcc \
        cmake \
        make \
        build-essential && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create log directories for proper logging
RUN mkdir -p /home/openai-forward/logs && \
    mkdir -p /home/openai-forward/webui-logs && \
    chmod 755 /home/openai-forward/logs && \
    chmod 755 /home/openai-forward/webui-logs

# Expose ports for API and WebUI services
# Port 8000: Main OpenAI Forward API endpoint
# Port 8001: Streamlit WebUI interface
EXPOSE 8000 8001

# Health check for service monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Set proper user permissions for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /home/openai-forward
USER appuser

# Entry point with WebUI enabled
# This starts both the API server and WebUI interface
ENTRYPOINT ["python3", "-m", "openai_forward.__main__", "run", "--webui"]

# ==============================================================================
# Usage Instructions:
#
# Build the WebUI image:
#   docker build -f webui.Dockerfile -t openai-forward-webui:latest .
#
# Run with WebUI enabled:
#   docker run -d -p 8000:8000 -p 8001:8001 \
#     --name openai-forward-webui \
#     -v ./openai-forward-config.yaml:/home/openai-forward/openai-forward-config.yaml:ro \
#     -v ./logs:/home/openai-forward/logs \
#     openai-forward-webui:latest
#
# Access the services:
#   - API: http://localhost:8000
#   - WebUI: http://localhost:8001
#
# Health check:
#   curl http://localhost:8000/healthz
# ==============================================================================
