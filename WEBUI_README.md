# OpenAI Forward WebUI Integration Guide

## Overview

This guide provides comprehensive instructions for setting up and using the OpenAI Forward WebUI interface. The WebUI provides a user-friendly web interface for configuring, monitoring, and managing your OpenAI Forward proxy service.

## Features

### 🎯 Core WebUI Features
- **Real-time Configuration Management** - Modify settings through an intuitive web interface
- **Live Monitoring** - View real-time logs and system activity
- **API Playground** - Test API endpoints directly from the browser
- **Usage Statistics** - Monitor request patterns and performance metrics
- **Multi-service Support** - Manage multiple AI providers (OpenAI, DeepSeek, LingyiWanwu, Ollama)
- **Docker Integration** - Full containerization support with health checks

### 🔧 Configuration Sections
1. **Forward Configuration** - Set up API forwarding rules and endpoints
2. **API Key & Level Management** - Configure access control and permissions
3. **Cache Settings** - Configure response caching for improved performance
4. **Rate Limiting** - Set up request rate controls and throttling
5. **Real-time Logs** - Monitor system activity and debug issues
6. **Playground** - Interactive API testing environment
7. **Statistics** - View detailed usage analytics and metrics

## Quick Start

### Method 1: Direct Python Execution

```bash
# Install dependencies
pip install -e ".[webui]"

# Start WebUI with API server
python -m openai_forward.__main__ run --webui --port 8000 --ui_port 8001

# Access the WebUI
open http://localhost:8001
```

### Method 2: Docker Compose (Recommended)

```bash
# Start all services including WebUI
docker-compose up -d

# Access the WebUI
open http://localhost:8001

# View logs
docker-compose logs -f openai-forward-webui
```

### Method 3: Standalone Docker

```bash
# Build the WebUI image
docker build -f webui.Dockerfile -t openai-forward-webui:latest .

# Run the WebUI container
docker run -d -p 8000:8000 -p 8001:8001 \
  --name openai-forward-webui \
  -v ./openai-forward-config.yaml:/home/openai-forward/openai-forward-config.yaml:ro \
  -v ./logs:/home/openai-forward/logs \
  openai-forward-webui:latest
```

## Service Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| 🌐 **WebUI Interface** | http://localhost:8001 | Main web interface |
| 🔧 **API Server** | http://localhost:8000 | OpenAI Forward API |
| 🏥 **Health Check** | http://localhost:8000/healthz | Service health status |
| 📊 **WebUI Health** | http://localhost:8001/_stcore/health | WebUI health status |

## Configuration Management

### Using the WebUI

1. **Access the Interface**
   - Open your browser to http://localhost:8001
   - Use the sidebar to navigate between sections

2. **Modify Configuration**
   - Edit settings using interactive forms
   - Use data editors for complex configurations
   - Preview changes before applying

3. **Apply Changes**
   - Click "Apply and Restart" to save and reload
   - Monitor the restart process in real-time logs
   - Verify changes in the configuration sections

### Configuration Sections Detail

#### Forward Configuration
```yaml
forward:
  - base_url: "https://api.openai.com"
    route: "/"
    type: "openai"
  - base_url: "https://api.deepseek.com"
    route: "/deepseek"
    type: "openai"
```

#### API Key Management
- Configure access levels and permissions
- Set up forward keys and service keys
- Define model access restrictions per level

#### Cache Settings
- Enable/disable response caching
- Configure cache TTL and storage
- Set cache rules per endpoint

#### Rate Limiting
- Configure request rate limits
- Set up per-user and global limits
- Define burst allowances

## Docker Integration

### Enhanced Dockerfile Features

The `webui.Dockerfile` includes:

```dockerfile
# Multi-stage build for optimized image size
FROM python:3.10-slim

# Security: Non-root user execution
USER appuser

# Health checks for monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Proper logging and timezone configuration
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1
```

### Docker Compose Configuration

The enhanced `docker-compose.yaml` provides:

```yaml
services:
  openai-forward-webui:
    build:
      context: .
      dockerfile: webui.Dockerfile
    ports:
      - "8001:8001"
    environment:
      - OPENAI_FORWARD_HOST=openai-forward
      - STREAMLIT_SERVER_PORT=8001
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/_stcore/health"]
    depends_on:
      openai-forward:
        condition: service_started
```

## Testing and Validation

### Automated Testing

Run the comprehensive test suite:

```bash
# Run WebUI Docker integration tests
python test_webui_docker.py

# Run WebUI demonstration
python webui_demo.py

# Run existing test suite
python -m pytest tests/ -v
```

### Manual Testing

1. **Service Health Checks**
   ```bash
   curl http://localhost:8001/_stcore/health
   curl http://localhost:8000/healthz
   ```

2. **WebUI Accessibility**
   ```bash
   curl -s http://localhost:8001 | grep -i streamlit
   ```

3. **Configuration Management**
   - Access WebUI at http://localhost:8001
   - Navigate through all configuration sections
   - Test "Apply and Restart" functionality

## Monitoring and Logging

### Real-time Logs

The WebUI provides real-time log monitoring:

1. **Access Logs Section**
   - Navigate to "Real-time Logs" in the sidebar
   - View live system activity
   - Filter logs by level and service

2. **Log Aggregation**
   - API server logs
   - WebUI application logs
   - Configuration change logs
   - Error and warning notifications

### Statistics Dashboard

Monitor system performance:

1. **Request Metrics**
   - Total requests processed
   - Response times and latency
   - Error rates and status codes

2. **Usage Analytics**
   - API key usage patterns
   - Model usage statistics
   - Rate limiting effectiveness

## Troubleshooting

### Common Issues

#### WebUI Not Accessible

```bash
# Check if service is running
curl http://localhost:8001/_stcore/health

# Check process status
ps aux | grep streamlit

# Restart service
python -m openai_forward.__main__ run --webui --port 8000 --ui_port 8001
```

#### Configuration Changes Not Applied

1. **Check WebUI Logs**
   - View real-time logs for error messages
   - Verify configuration syntax

2. **Manual Configuration Reload**
   ```bash
   # Restart the service
   docker-compose restart openai-forward-webui
   ```

#### Docker Build Issues

```bash
# Clean Docker cache
docker system prune -a

# Rebuild with no cache
docker build --no-cache -f webui.Dockerfile -t openai-forward-webui .
```

### Debug Mode

Enable debug logging:

```bash
# Set debug environment
export LOG_LEVEL=DEBUG

# Run with verbose logging
python -m openai_forward.__main__ run --webui --port 8000 --ui_port 8001
```

## Security Considerations

### Access Control

1. **Network Security**
   - Bind WebUI to localhost for local access only
   - Use reverse proxy for external access
   - Implement SSL/TLS for production

2. **Authentication**
   - Configure API key authentication
   - Set up user access levels
   - Monitor access logs

### Container Security

1. **Non-root Execution**
   - WebUI runs as non-root user (appuser)
   - Minimal container privileges

2. **Resource Limits**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 512M
         cpus: '0.3'
   ```

## Performance Optimization

### Resource Management

1. **Memory Usage**
   - Monitor WebUI memory consumption
   - Configure appropriate container limits
   - Use caching for improved performance

2. **CPU Optimization**
   - Limit CPU usage for WebUI container
   - Use efficient data processing
   - Implement request queuing

### Scaling Considerations

1. **Horizontal Scaling**
   - Deploy multiple WebUI instances
   - Use load balancer for distribution
   - Implement session persistence

2. **Vertical Scaling**
   - Increase container resources
   - Optimize database connections
   - Use connection pooling

## Development and Customization

### Extending the WebUI

1. **Custom Components**
   - Add new configuration sections
   - Implement custom visualizations
   - Create specialized monitoring dashboards

2. **API Integration**
   - Extend API endpoint testing
   - Add new service integrations
   - Implement custom metrics

### Contributing

1. **Code Standards**
   - Follow existing code style
   - Add comprehensive comments
   - Include error handling

2. **Testing Requirements**
   - Write unit tests for new features
   - Update integration tests
   - Verify Docker compatibility

## Support and Resources

### Documentation

- [OpenAI Forward Main Documentation](README.md)
- [API Authentication Guide](API_AUTHENTICATION_GUIDE.md)
- [Multi-AI Setup Guide](README_MULTI_AI.md)

### Community

- [GitHub Issues](https://github.com/KenyonY/openai-forward/issues)
- [Discussions](https://github.com/KenyonY/openai-forward/discussions)
- [Contributing Guidelines](CONTRIBUTING.md)

### Version Information

- **WebUI Version**: 2.0
- **OpenAI Forward Compatibility**: Latest
- **Docker Support**: Full
- **Last Updated**: 2024-12-19

---

## Quick Reference Commands

```bash
# Start WebUI
python -m openai_forward.__main__ run --webui

# Docker build
docker build -f webui.Dockerfile -t openai-forward-webui .

# Docker compose
docker-compose up openai-forward-webui -d

# Health check
curl http://localhost:8001/_stcore/health

# View logs
docker-compose logs -f openai-forward-webui

# Run tests
python test_webui_docker.py
```

For additional help and support, please refer to the main project documentation or open an issue on GitHub. 