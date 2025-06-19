# 🌐 Remote Ollama Server Configuration Guide

## 📋 Overview

This guide helps you configure the AI Gateway to use a **remote Ollama server** instead of running Ollama locally in Docker. This is particularly useful for:

- **Dedicated GPU Servers**: Running Ollama on a high-performance GPU server
- **Resource Optimization**: Separating compute-intensive AI models from the gateway
- **Scalability**: Multiple gateway instances connecting to centralized Ollama servers
- **Network Architecture**: Different deployment strategies in enterprise environments

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   AI Gateway    │    │ Remote Ollama   │
│                 │    │                 │    │                 │
│ • Web Apps      │───▶│ • NGINX Gateway │───▶│ • GPU Server    │
│ • Mobile Apps   │    │ • OpenAI Proxy  │    │ • Model Storage │
│ • CLI Tools     │    │ • Smart Router  │    │ • Inference     │
│ • APIs          │    │ • WebUI         │    │ • API Endpoint  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              :8000                  :11434
```

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

Run the automated setup script:

```bash
# Make script executable (if not already)
chmod +x setup_remote_ollama.sh

# Run setup wizard
./setup_remote_ollama.sh
```

The script will:
1. ✅ Check dependencies (Docker, curl, Python)
2. 🔗 Test connection to your remote Ollama server
3. ⚙️ Generate configuration files
4. 🚀 Start all services with remote Ollama

### Option 2: Manual Setup

#### Step 1: Test Remote Connection

```bash
# Test your remote Ollama server
python3 test_remote_ollama.py http://YOUR_REMOTE_IP:11434

# Example:
python3 test_remote_ollama.py http://192.168.1.100:11434
```

#### Step 2: Configure Environment

Create `.env` file:

```bash
# Remote Ollama Server Configuration
OLLAMA_REMOTE_URL=http://192.168.1.100:11434

# API Keys (optional)
OPENAI_API_KEY=sk-your-openai-key-here
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
LINGYIWANWU_API_KEY=your-lingyiwanwu-key-here

# Performance Settings
OLLAMA_TIMEOUT=60
CONNECTION_RETRIES=3
```

#### Step 3: Update Configuration

Update `openai-forward-config-remote-ollama.yaml`:

```yaml
forward:
  # Remote Ollama Server
  - base_url: "http://192.168.1.100:11434"
    route: "/ollama"
    type: "general"
    timeout: 60
```

#### Step 4: Start Services

```bash
# Start with remote Ollama configuration
docker-compose -f docker-compose-remote-ollama.yaml up -d

# Monitor startup
docker-compose -f docker-compose-remote-ollama.yaml logs -f
```

## 🔧 Remote Ollama Server Setup

### On Your Remote Server (GPU Server)

#### 1. Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Or manually download
# wget https://ollama.com/download/ollama-linux-amd64
# sudo mv ollama-linux-amd64 /usr/local/bin/ollama
# sudo chmod +x /usr/local/bin/ollama
```

#### 2. Configure Ollama for Remote Access

```bash
# Create systemd service for network access
sudo tee /etc/systemd/system/ollama.service > /dev/null <<EOF
[Unit]
Description=Ollama Server
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_PORT=11434"

[Install]
WantedBy=default.target
EOF

# Create ollama user
sudo useradd -r -s /bin/false -m -d /usr/share/ollama ollama

# Start and enable service
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama
```

#### 3. Install Models

```bash
# Install popular models
ollama pull llama3.2
ollama pull qwen2:1.5b
ollama pull codegemma

# List installed models
ollama list
```

#### 4. Configure Firewall

```bash
# Ubuntu/Debian
sudo ufw allow 11434/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=11434/tcp
sudo firewall-cmd --reload

# Or disable firewall temporarily (not recommended for production)
sudo systemctl stop ufw  # Ubuntu
sudo systemctl stop firewalld  # CentOS
```

#### 5. Verify Remote Access

```bash
# Test from another machine
curl http://YOUR_SERVER_IP:11434/api/tags

# Should return JSON with model list
```

## 📊 Service Endpoints

Once configured, your services will be available at:

| Service | URL | Description |
|---------|-----|-------------|
| **AI Gateway** | `http://localhost` | NGINX gateway with load balancing |
| **OpenAI Proxy** | `http://localhost:8000` | Main proxy service |
| **WebUI** | `http://localhost:8001` | Configuration management |
| **Smart Router** | `http://localhost:9000` | Intelligent request routing |
| **Monitoring** | `http://localhost:8002` | System health dashboard |

## 🔌 API Usage Examples

### Via NGINX Gateway (Recommended)

```bash
# Chat completion with remote Ollama
curl -X POST http://localhost/ollama/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "Hello, how are you?"}],
    "stream": false
  }'
```

### Direct to OpenAI Forward

```bash
# Direct API call
curl -X POST http://localhost:8000/ollama/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" \
  -d '{
    "model": "qwen2:1.5b",
    "messages": [{"role": "user", "content": "Write a Python function"}]
  }'
```

### Python Client Example

```python
import requests

def chat_with_ollama(message, model="llama3.2"):
    """Chat with remote Ollama via AI Gateway"""
    
    response = requests.post(
        "http://localhost/ollama/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "stream": False
        }
    )
    
    return response.json()

# Usage
result = chat_with_ollama("Explain quantum computing")
print(result['choices'][0]['message']['content'])
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Connection Refused

**Problem**: Cannot connect to remote Ollama server

**Solutions**:
```bash
# Check if Ollama is running
ssh user@remote-server "systemctl status ollama"

# Check if port is open
nc -zv REMOTE_IP 11434

# Check firewall
ssh user@remote-server "sudo ufw status"  # Ubuntu
ssh user@remote-server "sudo firewall-cmd --list-ports"  # CentOS
```

#### 2. Timeout Errors

**Problem**: Requests timeout to remote server

**Solutions**:
- Increase timeout in configuration:
```yaml
# In openai-forward-config-remote-ollama.yaml
forward:
  - base_url: "http://REMOTE_IP:11434"
    timeout: 120  # Increase from 60 to 120 seconds
```

- Check network latency:
```bash
python3 test_remote_ollama.py http://REMOTE_IP:11434
```

#### 3. Model Not Found

**Problem**: "Model not found" errors

**Solutions**:
```bash
# On remote server, install missing models
ssh user@remote-server "ollama pull llama3.2"

# List available models
curl http://REMOTE_IP:11434/api/tags
```

#### 4. High Latency

**Problem**: Slow response times

**Solutions**:
- Use local network instead of internet
- Optimize network configuration
- Consider model quantization on remote server

### Debug Commands

```bash
# Check service logs
docker-compose -f docker-compose-remote-ollama.yaml logs openai-forward
docker-compose -f docker-compose-remote-ollama.yaml logs ai-router

# Test individual services
curl -v http://localhost:8000/health
curl -v http://localhost:8001/health

# Monitor system resources
python3 monitor_system.py
```

## 🔐 Security Considerations

### Network Security

1. **Use Private Networks**: Deploy on private VLANs or VPNs
2. **Firewall Rules**: Restrict access to port 11434
3. **SSH Tunneling**: For secure remote access

```bash
# SSH tunnel example
ssh -L 11434:localhost:11434 user@remote-server
# Then use: http://localhost:11434 in gateway config
```

### Authentication

1. **API Key Protection**: Use environment variables
2. **Network Access Control**: Restrict by IP addresses
3. **TLS/SSL**: Use HTTPS for production deployments

## 📈 Performance Optimization

### Network Optimization

1. **Connection Pooling**: Configured in docker-compose
2. **Keep-Alive**: Enabled by default
3. **Compression**: NGINX gzip compression

### Ollama Server Optimization

```bash
# On remote server - optimize for performance
export OLLAMA_NUM_PARALLEL=4        # Parallel requests
export OLLAMA_MAX_LOADED_MODELS=3   # Max models in memory
export OLLAMA_FLASH_ATTENTION=1     # Enable flash attention
```

### Monitoring and Alerts

```bash
# Set up monitoring
python3 monitor_system.py &

# Monitor remote Ollama health
watch -n 30 "curl -s http://REMOTE_IP:11434/api/tags | jq '.models | length'"
```

## 🚀 Production Deployment

### High Availability Setup

1. **Multiple Ollama Servers**: Load balance across multiple instances
2. **Health Checks**: Automatic failover on server failure
3. **Model Synchronization**: Keep models in sync across servers

### Scaling Configuration

```yaml
# Multiple Ollama servers in openai-forward-config.yaml
forward:
  - base_url: "http://ollama-1.internal:11434"
    route: "/ollama"
    type: "general"
    weight: 1
    
  - base_url: "http://ollama-2.internal:11434"
    route: "/ollama-backup"
    type: "general"
    weight: 2
```

## 📝 Management Commands

```bash
# Service Management
docker-compose -f docker-compose-remote-ollama.yaml up -d      # Start all services
docker-compose -f docker-compose-remote-ollama.yaml down       # Stop all services
docker-compose -f docker-compose-remote-ollama.yaml restart    # Restart services
docker-compose -f docker-compose-remote-ollama.yaml logs -f    # View logs

# Configuration Update
./setup_remote_ollama.sh                                       # Re-run setup
python3 test_remote_ollama.py http://NEW_IP:11434              # Test new server

# Health Monitoring
curl http://localhost/health                                    # Gateway health
curl http://REMOTE_IP:11434/api/tags                          # Ollama health
python3 monitor_system.py                                      # System dashboard
```

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose -f docker-compose-remote-ollama.yaml logs`
2. Test connectivity: `python3 test_remote_ollama.py http://YOUR_IP:11434`
3. Review configuration: Verify `.env` and YAML files
4. Monitor resources: Use `python3 monitor_system.py`

## 🎉 Next Steps

Once your remote Ollama setup is working:

1. **Add More Models**: Install additional models on your remote server
2. **Scale Horizontally**: Add more Ollama servers for load distribution  
3. **Enable HTTPS**: Configure SSL certificates for production
4. **Set Up Monitoring**: Implement comprehensive logging and alerting
5. **Backup Strategy**: Plan for model and configuration backups

---

**🌟 Your AI Gateway is now connected to remote Ollama server!** 

Enjoy the flexibility of distributed AI services with centralized management. 🚀 