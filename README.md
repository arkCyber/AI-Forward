# 🚀 AI-Forward

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/arkCyber/AI-Forward?style=social)
![GitHub forks](https://img.shields.io/github/forks/arkCyber/AI-Forward?style=social)
![GitHub issues](https://img.shields.io/github/issues/arkCyber/AI-Forward)
![GitHub license](https://img.shields.io/github/license/arkCyber/AI-Forward)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![NGINX](https://img.shields.io/badge/nginx-%23009639.svg?style=flat&logo=nginx&logoColor=white)

**🌟 Enterprise-Grade Multi-AI Gateway with NGINX Load Balancing**

*A high-performance, scalable AI service proxy supporting multiple providers*

[🚀 Quick Start](#quick-start) • 
[📖 Documentation](#documentation) • 
[🎯 Features](#features) • 
[🐛 Issues](https://github.com/arkCyber/AI-Forward/issues) • 
[🤝 Contributing](#contributing)

</div>

---

## 🎯 Features

### 🌐 Multi-AI Provider Support
- **🤖 DeepSeek AI** - Advanced reasoning and coding capabilities
- **🧠 LingyiWanwu (零一万物)** - Chinese-optimized language models  
- **🦙 Ollama** - Local open-source models (Llama, Qwen, CodeGemma)
- **🔥 OpenAI** - GPT models support
- **➕ Extensible** - Easy to add new providers

### 🚀 Enterprise-Grade Infrastructure
- **⚡ NGINX Load Balancer** - High-performance reverse proxy
- **🛡️ Rate Limiting** - Multi-tier rate limiting (100 API/min, 60 chat/min)
- **📊 Real-time Monitoring** - Health checks and performance metrics
- **🔄 Auto Failover** - Automatic service recovery and routing
- **📦 Docker Containerized** - Easy deployment and scaling

### 🎛️ Management & Monitoring
- **🖥️ WebUI Dashboard** - Visual configuration and monitoring
- **📈 Load Testing** - Built-in multi-user testing tools
- **🔍 System Monitor** - Real-time service status dashboard
- **📊 Statistics** - Usage analytics and performance metrics

### 🔒 Security & Performance
- **🔐 API Key Management** - Secure authentication system
- **🗜️ Compression** - Gzip compression for bandwidth optimization
- **⚡ Connection Pooling** - HTTP/1.1 keepalive optimization
- **🛡️ Security Headers** - XSS protection, content type validation

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for monitoring tools)
- 4GB+ RAM recommended

### 1️⃣ Clone Repository
```bash
git clone https://github.com/arkCyber/AI-Forward.git
cd AI-Forward
```

### 2️⃣ Configure Services
```bash
# Copy and edit configuration
cp openai-forward-config.example.yaml openai-forward-config.yaml
# Edit with your API keys
```

### 3️⃣ Start All Services
```bash
# Start the complete stack
docker-compose up -d

# Check service status
docker-compose ps
```

### 4️⃣ Access Services
- **🎯 Main API**: `http://localhost/api/v1/chat/completions`
- **🖥️ WebUI**: `http://localhost/webui/`
- **📊 Health Check**: `http://localhost/health`
- **📈 Statistics**: `http://localhost/stats`

---

## 📖 Documentation

### 🔧 API Usage

#### Unified API Endpoint (Recommended)
```bash
curl -X POST http://localhost/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

#### Service-Specific Endpoints
```bash
# DeepSeek AI
curl -X POST http://localhost/deepseek/v1/chat/completions

# LingyiWanwu (零一万物)  
curl -X POST http://localhost/lingyiwanwu/v1/chat/completions

# Ollama Local Models
curl -X POST http://localhost/ollama/v1/chat/completions

# OpenAI
curl -X POST http://localhost/forward/v1/chat/completions
```

### 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| NGINX Gateway | 80, 443 | Load balancer & reverse proxy |
| AI Router | 9000 | Unified API endpoint |
| OpenAI Forward | 8000 | Multi-provider proxy |
| WebUI | 8001 | Management interface |
| Ollama | 11434 | Local AI models |

### 📊 Monitoring & Testing

#### Real-time System Monitor
```bash
# Install dependencies
pip install aiohttp

# Start monitoring dashboard
python monitor_system.py
```

#### Multi-user Load Testing
```bash
# Run load test with 10 concurrent users
python test_multiuser.py
```

---

## 🛠️ Management Commands

```bash
# View all services
docker-compose ps

# View logs
docker-compose logs -f nginx
docker-compose logs -f ai-router

# Restart services
docker-compose restart

# Stop all services
docker-compose down

# Download Ollama models
docker exec -it ollama-server ollama pull llama3.2:1b
docker exec -it ollama-server ollama pull qwen2:1.5b
```

---

## 🏗️ Architecture

```
Internet/Users → NGINX Gateway (Port 80/443) → Backend Services
                     ↓
          ┌─────────────────────────────────┐
          │     Load Balancing              │
          │     Rate Limiting               │
          │     SSL Termination             │
          │     Security Headers            │
          │     Compression                 │
          └─────────────────────────────────┘
                     ↓
    ┌────────────────┬────────────────┬─────────────────┐
    │   AI Router    │ OpenAI Forward │     WebUI       │
    │   (Port 9000)  │  (Port 8000)   │  (Port 8001)    │
    └────────────────┴────────────────┴─────────────────┘
                     ↓
                ┌─────────────┐
                │   Ollama    │
                │ (Port 11434)│
                └─────────────┘
```

---

## 📈 Performance Features

### 🚀 Multi-User Capabilities
- **Rate Limiting**: 100 API calls/min, 60 chat/min per IP
- **Connection Limits**: Max 50 concurrent connections per IP  
- **Load Balancing**: Automatic request distribution
- **Auto Scaling**: Easy horizontal scaling support

### ⚡ Optimization
- **Gzip Compression**: Reduces bandwidth by 60-80%
- **Connection Pooling**: HTTP/1.1 keepalive optimization
- **Caching**: Intelligent response caching (FlaxKV)
- **Async Processing**: High-concurrency request handling

---

## 🔧 Configuration

### Key Configuration Files
- `nginx.conf` - NGINX load balancer settings
- `docker-compose.yaml` - Service orchestration
- `openai-forward-config.yaml` - AI provider configuration
- `.env` - Environment variables

### Environment Variables
```bash
# API Keys
DEEPSEEK_API_KEY=your_deepseek_key
LINGYIWANWU_API_KEY=your_lingyiwanwu_key
OPENAI_API_KEY=your_openai_key

# Service Configuration
NGINX_WORKER_PROCESSES=auto
LOG_LEVEL=INFO
```

---

## 🚀 Production Deployment

### 🔒 Security Recommendations
1. **Enable HTTPS** - Add SSL certificates
2. **Firewall Rules** - Restrict access to necessary ports
3. **API Key Rotation** - Regular key updates
4. **Access Logs** - Enable comprehensive logging

### 📊 Monitoring Setup
1. **Prometheus + Grafana** - Metrics collection
2. **ELK Stack** - Log analysis
3. **Alerting** - Service health alerts
4. **Backup Strategy** - Configuration and data backup

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### 🐛 Bug Reports
- Use [GitHub Issues](https://github.com/arkCyber/AI-Forward/issues)
- Include system info and error logs
- Provide reproduction steps

### 💡 Feature Requests
- Open a GitHub Issue with the `enhancement` label
- Describe the use case and expected behavior
- Consider submitting a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [OpenAI Forward](https://github.com/KenyonY/openai-forward) - Original project base
- [NGINX](https://nginx.org/) - High-performance web server
- [Ollama](https://ollama.ai/) - Local AI model runtime
- [Docker](https://docker.com/) - Containerization platform

---

## 📞 Support

- 📧 Email: arksong2018@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/arkCyber/AI-Forward/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/arkCyber/AI-Forward/discussions)

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

Made with ❤️ by [arkSong](https://github.com/arkSong)

</div>
