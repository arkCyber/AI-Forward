# OpenAI Forward Multi-AI Provider Setup

**Author:** Assistant  
**Created:** 2024-12-19  
**Version:** 1.0  

## 📋 Overview

This configuration sets up OpenAI Forward to proxy multiple AI services through OpenAI-compatible interfaces:

- **DeepSeek AI** - `https://api.deepseek.com`
- **零一万物 (LingyiWanwu)** - `https://api.lingyiwanwu.com/v1`
- **OpenAI** - `https://api.openai.com` (optional)

All services are accessible through a unified proxy with rate limiting, caching, and comprehensive logging.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- API keys for the services you want to use
- Port 8000 available on your system

### 1. Start the Service

```bash
# Make the script executable (if not already done)
chmod +x start.sh

# Start the service
./start.sh start
```

### 2. Verify Service is Running

```bash
# Check service status
./start.sh status

# View real-time logs
./start.sh logs
```

### 3. Test the APIs

#### Test DeepSeek API
```bash
curl -X POST http://localhost:8000/deepseek/v1/chat/completions \
  -H "Authorization: Bearer sk-878a5319c7b14bc48109e19315361b7f" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [
      {
        "role": "user",
        "content": "Hello, how are you?"
      }
    ],
    "max_tokens": 100
  }'
```

#### Test LingyiWanwu API
```bash
curl -X POST http://localhost:8000/lingyiwanwu/v1/chat/completions \
  -H "Authorization: Bearer 72ebf8a6191e45bab0f646659c8cb121" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "yi-34b-chat",
    "messages": [
      {
        "role": "user",
        "content": "你好，请介绍一下你自己"
      }
    ],
    "max_tokens": 100
  }'
```

## 🔧 Service Endpoints

| Service | Endpoint | API Key |
|---------|----------|---------|
| DeepSeek | `http://localhost:8000/deepseek/v1/chat/completions` | `sk-878a5319c7b14bc48109e19315361b7f` |
| LingyiWanwu | `http://localhost:8000/lingyiwanwu/v1/chat/completions` | `72ebf8a6191e45bab0f646659c8cb121` |
| OpenAI | `http://localhost:8000/v1/chat/completions` | Your OpenAI key |
| Health Check | `http://localhost:8000/health` | - |

## 📚 Client Integration Examples

### Python with OpenAI Library

```python
from openai import OpenAI
import logging
from datetime import datetime

# Setup logging with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_deepseek_api():
    """Test DeepSeek API integration with error handling"""
    try:
        logger.info("Initializing DeepSeek client...")
        client = OpenAI(
            base_url="http://localhost:8000/deepseek/v1",
            api_key="sk-878a5319c7b14bc48109e19315361b7f"
        )
        
        logger.info("Sending request to DeepSeek...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": "Explain quantum computing"}
            ],
            max_tokens=150
        )
        
        logger.info("DeepSeek response received successfully")
        print(f"DeepSeek Response: {response.choices[0].message.content}")
        return response
        
    except Exception as e:
        logger.error(f"Error calling DeepSeek API: {str(e)}")
        raise

def test_lingyiwanwu_api():
    """Test LingyiWanwu API integration with error handling"""
    try:
        logger.info("Initializing LingyiWanwu client...")
        client = OpenAI(
            base_url="http://localhost:8000/lingyiwanwu/v1",
            api_key="72ebf8a6191e45bab0f646659c8cb121"
        )
        
        logger.info("Sending request to LingyiWanwu...")
        response = client.chat.completions.create(
            model="yi-34b-chat",
            messages=[
                {"role": "user", "content": "请解释人工智能的发展历程"}
            ],
            max_tokens=150
        )
        
        logger.info("LingyiWanwu response received successfully")
        print(f"LingyiWanwu Response: {response.choices[0].message.content}")
        return response
        
    except Exception as e:
        logger.error(f"Error calling LingyiWanwu API: {str(e)}")
        raise

if __name__ == "__main__":
    print("Testing Multi-AI Provider Setup...")
    print(f"Timestamp: {datetime.now()}")
    
    # Test both APIs
    test_deepseek_api()
    test_lingyiwanwu_api()
```

### JavaScript/Node.js Example

```javascript
const OpenAI = require('openai');

// DeepSeek client with error handling
const deepseekClient = new OpenAI({
  baseURL: 'http://localhost:8000/deepseek/v1',
  apiKey: 'sk-878a5319c7b14bc48109e19315361b7f',
});

// LingyiWanwu client with error handling
const lingyiwanwuClient = new OpenAI({
  baseURL: 'http://localhost:8000/lingyiwanwu/v1',
  apiKey: '72ebf8a6191e45bab0f646659c8cb121',
});

async function testDeepSeek() {
  try {
    console.log(`[${new Date().toISOString()}] Testing DeepSeek API...`);
    
    const response = await deepseekClient.chat.completions.create({
      model: 'deepseek-chat',
      messages: [
        { role: 'user', content: 'What is machine learning?' }
      ],
      max_tokens: 100,
    });
    
    console.log('DeepSeek Response:', response.choices[0].message.content);
    return response;
  } catch (error) {
    console.error(`[${new Date().toISOString()}] DeepSeek API Error:`, error.message);
    throw error;
  }
}

async function testLingyiWanwu() {
  try {
    console.log(`[${new Date().toISOString()}] Testing LingyiWanwu API...`);
    
    const response = await lingyiwanwuClient.chat.completions.create({
      model: 'yi-34b-chat',
      messages: [
        { role: 'user', content: '什么是深度学习？' }
      ],
      max_tokens: 100,
    });
    
    console.log('LingyiWanwu Response:', response.choices[0].message.content);
    return response;
  } catch (error) {
    console.error(`[${new Date().toISOString()}] LingyiWanwu API Error:`, error.message);
    throw error;
  }
}

// Run tests
async function main() {
  console.log('Starting Multi-AI Provider Tests...');
  await testDeepSeek();
  await testLingyiWanwu();
  console.log('All tests completed!');
}

main().catch(console.error);
```

## 🛠️ Management Commands

```bash
# Start the service
./start.sh start

# Stop the service
./start.sh stop

# Restart the service
./start.sh restart

# Check service status
./start.sh status

# View logs in real-time
./start.sh logs

# Show service information
./start.sh info

# Get help
./start.sh help
```

## 📊 Service Configuration

### Rate Limits
- **Global:** 200 requests/minute
- **DeepSeek:** 80 requests/2 minutes, 80 tokens/second
- **LingyiWanwu:** 60 requests/2 minutes, 60 tokens/second

### Caching
- **Backend:** Memory-based (MEMORY)
- **Cache Routes:** `/v1/chat/completions`, `/v1/embeddings`
- **Storage:** `./FLAXKV_DB` directory

### Logging
- **Format:** JSON with timestamps
- **Rotation:** 10MB max size, 3 files kept
- **Location:** `./logs` directory

## 🔍 Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check Docker status
docker info

# Check if port 8000 is in use
lsof -i :8000

# View detailed logs
./start.sh logs
```

#### 2. API Key Issues
- Verify API keys are correct in `openai-forward-config.yaml`
- Check if keys have sufficient permissions
- Ensure keys are not expired

#### 3. Connection Errors
```bash
# Test connectivity to upstream services
curl -I https://api.deepseek.com
curl -I https://api.lingyiwanwu.com/v1

# Check service health
curl http://localhost:8000/health
```

#### 4. Performance Issues
- Monitor service logs for rate limit warnings
- Check cache hit rates in logs
- Verify resource limits in `docker-compose.yaml`

### Log Analysis

```bash
# Follow all logs
docker-compose logs -f

# Filter specific service logs
docker-compose logs -f openai-forward

# Search for errors
docker-compose logs | grep -i error

# Check last 100 lines
docker-compose logs --tail=100
```

## 🔧 Advanced Configuration

### Custom Model Mapping
Edit `openai-forward-config.yaml` to add custom model mappings:

```yaml
api_key:
  level:
    0: ["deepseek-chat", "deepseek-coder", "custom-model"]
    1: ["yi-34b-chat", "yi-6b-chat", "another-model"]
```

### Additional Rate Limits
```yaml
rate_limit:
  req_rate_limit:
    - route: "/custom/v1/chat/completions"
      value:
      - level: 0
        limit: "50/minute"
```

### Environment Variables
Set these in your shell or add to `.env` file:

```bash
export LOG_LEVEL=DEBUG
export CACHE_BACKEND=LMDB
export RATE_LIMIT_BACKEND=redis://localhost:6379
```

## 📈 Monitoring

### Health Checks
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed service status
./start.sh status

# Container resource usage
docker stats openai-forward-proxy
```

### Metrics Collection
The service provides detailed logs for monitoring:
- Request counts per endpoint
- Response times
- Error rates
- Cache hit/miss ratios

## 🔒 Security Considerations

1. **API Key Security**
   - Store keys in environment variables for production
   - Rotate keys regularly
   - Monitor usage for suspicious activity

2. **Network Security**
   - Use HTTPS in production
   - Implement IP whitelisting if needed
   - Consider using a reverse proxy

3. **Access Control**
   - Configure rate limits appropriately
   - Monitor for abuse patterns
   - Implement forward keys for additional security

## 📝 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review service logs: `./start.sh logs`
3. Verify configuration in `openai-forward-config.yaml`
4. Test individual API endpoints directly

---

**Last Updated:** 2024-12-19  
**Configuration Version:** 1.0 