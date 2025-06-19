# 🚀 AI-Forward Deployment Guide

This comprehensive guide will help you deploy the AI-Forward system in various environments.

## 📋 Prerequisites

### System Requirements
- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Python** 3.10+ (for monitoring tools)
- **Memory**: 4GB+ RAM recommended
- **Storage**: 10GB+ available space
- **Network**: Internet access for AI provider APIs

### API Keys (Choose your providers)
- **DeepSeek AI**: Get API key from [DeepSeek Console](https://platform.deepseek.com/)
- **LingyiWanwu (零一万物)**: Get API key from [LingyiWanwu Platform](https://platform.lingyiwanwu.com/)
- **OpenAI**: Get API key from [OpenAI Platform](https://platform.openai.com/)

---

## 🎯 Quick Deployment (Recommended)

### 1. Clone Repository
```bash
git clone https://github.com/arkCyber/AI-Forward.git
cd AI-Forward
```

### 2. Configure API Keys
```bash
# Copy configuration template
cp openai-forward-config.example.yaml openai-forward-config.yaml

# Edit configuration file with your API keys
nano openai-forward-config.yaml
```

**Configuration Example:**
```yaml
# Add your API keys here
api_key:
  openai_key:
    "your-deepseek-api-key": [0]     # DeepSeek access
    "your-lingyiwanwu-api-key": [1]  # LingyiWanwu access  
    "your-openai-api-key": [2]       # OpenAI access
```

### 3. Start All Services
```bash
# Start the complete stack
docker-compose up -d

# Verify all services are running
docker-compose ps
```

### 4. Access Your AI Gateway
- **🎯 Main API**: `http://localhost/api/v1/chat/completions`
- **🖥️ WebUI**: `http://localhost/webui/`
- **📊 Health Check**: `http://localhost/health`

---

## 🔧 Advanced Configuration

### Environment Variables
Create a `.env` file for environment-specific settings:

```bash
# AI Provider API Keys
DEEPSEEK_API_KEY=your_deepseek_key
LINGYIWANWU_API_KEY=your_lingyiwanwu_key
OPENAI_API_KEY=your_openai_key

# Service Configuration
NGINX_WORKER_PROCESSES=auto
LOG_LEVEL=INFO
TZ=Asia/Shanghai

# Rate Limiting (requests per minute)
API_RATE_LIMIT=100
CHAT_RATE_LIMIT=60
WEBUI_RATE_LIMIT=30
```

### NGINX Configuration
Edit `nginx.conf` to customize:
- Rate limiting rules
- SSL certificates (production)
- Custom domains
- Security headers

### Docker Resources
Adjust resource limits in `docker-compose.yaml`:
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
```

---

## 🌐 Production Deployment

### 1. Enable HTTPS
```bash
# Generate SSL certificates (Let's Encrypt example)
certbot certonly --standalone -d your-domain.com

# Update nginx.conf to enable HTTPS block
# Uncomment and configure the HTTPS server section
```

### 2. Firewall Configuration
```bash
# Ubuntu/Debian
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 22    # SSH

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

### 3. Domain Configuration
Update your DNS records:
```
A     your-domain.com     YOUR_SERVER_IP
CNAME api.your-domain.com your-domain.com
```

### 4. Performance Optimization
```bash
# Increase system limits
echo "fs.file-max = 65535" >> /etc/sysctl.conf
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
sysctl -p
```

---

## 🐳 Docker Deployment Options

### Option 1: All-in-One (Recommended)
```bash
docker-compose up -d
```

### Option 2: Selective Services
```bash
# Start only core services
docker-compose up -d nginx ai-router openai-forward

# Add WebUI later
docker-compose up -d openai-forward-webui

# Add Ollama for local models
docker-compose up -d ollama
```

### Option 3: Scaling Services
```bash
# Scale AI Router for high load
docker-compose up -d --scale ai-router=3

# Scale OpenAI Forward
docker-compose up -d --scale openai-forward=2
```

---

## 📊 Monitoring & Logging

### 1. Real-time Monitoring
```bash
# Install monitoring dependencies
pip install aiohttp

# Start system monitor
python monitor_system.py
```

### 2. Service Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f nginx
docker-compose logs -f ai-router
docker-compose logs -f openai-forward
```

### 3. Load Testing
```bash
# Run multi-user load test
python test_multiuser.py

# Customize test parameters
python test_multiuser.py --users 20 --requests 5
```

---

## 🔄 Ollama Local Models

### 1. Download Models
```bash
# Download popular models
docker exec -it ollama-server ollama pull llama3.2:1b
docker exec -it ollama-server ollama pull qwen2:1.5b
docker exec -it ollama-server ollama pull codegemma:2b

# List available models
docker exec -it ollama-server ollama list
```

### 2. Custom Model Configuration
```bash
# Create custom Modelfile
echo "FROM llama3.2:1b
SYSTEM You are a helpful assistant." > Modelfile

# Build custom model
docker exec -it ollama-server ollama create mycustom -f Modelfile
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Services Won't Start
```bash
# Check Docker status
sudo systemctl status docker

# Check logs for errors
docker-compose logs

# Restart services
docker-compose restart
```

#### 2. Port Conflicts
```bash
# Check port usage
netstat -tlnp | grep :80
netstat -tlnp | grep :443

# Stop conflicting services
sudo systemctl stop apache2  # or nginx
```

#### 3. API Key Issues
```bash
# Validate configuration
docker-compose exec openai-forward python -c "
from openai_forward.config.settings import Settings
print(Settings().dict())
"
```

#### 4. Memory Issues
```bash
# Check system resources
docker stats

# Increase Docker memory limits
# Edit docker-compose.yaml memory settings
```

### Health Checks
```bash
# NGINX health
curl http://localhost/nginx-health

# Services health
curl http://localhost/health

# API test
curl -X POST http://localhost/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"test"}]}'
```

---

## 📈 Performance Tuning

### 1. NGINX Optimization
```nginx
# In nginx.conf
worker_processes auto;
worker_connections 4096;
keepalive_timeout 65;
client_max_body_size 100M;
```

### 2. Docker Optimization
```yaml
# In docker-compose.yaml
services:
  nginx:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

### 3. System Optimization
```bash
# Increase file limits
echo "* soft nofile 65535" >> /etc/security/limits.conf
echo "* hard nofile 65535" >> /etc/security/limits.conf

# Optimize TCP settings
echo "net.ipv4.tcp_fin_timeout = 30" >> /etc/sysctl.conf
echo "net.ipv4.tcp_keepalive_time = 120" >> /etc/sysctl.conf
```

---

## 🔐 Security Best Practices

### 1. API Key Security
- Rotate API keys regularly
- Use environment variables instead of config files
- Implement proper access controls

### 2. Network Security
```bash
# Use fail2ban for brute force protection
sudo apt install fail2ban

# Configure iptables
sudo iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
```

### 3. Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Docker images
docker-compose pull
docker-compose up -d
```

---

## 🌍 Cloud Deployment

### AWS EC2
```bash
# Launch instance with Docker pre-installed
# Security group: HTTP (80), HTTPS (443), SSH (22)

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Google Cloud Platform
```bash
# Use Container-Optimized OS
gcloud compute instances create ai-forward \
  --image-family cos-stable \
  --image-project cos-cloud \
  --machine-type e2-standard-2
```

### Digital Ocean
```bash
# Use Docker droplet
# Enable monitoring and backups
# Configure domain and SSL
```

---

## 📞 Support

For deployment issues:
- 📧 Email: arksong2018@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/arkCyber/AI-Forward/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/arkCyber/AI-Forward/discussions)

---

**✅ Deployment Complete!** Your AI-Forward gateway is now ready to handle enterprise-scale AI requests with NGINX load balancing and multi-provider support. 