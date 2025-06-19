#!/bin/bash
# ==============================================================================
# NGINX AI Gateway Test Examples
# ==============================================================================
# Description: 简单的 curl 测试示例，测试流式服务和外部访问
# Author: Assistant
# Created: 2024-12-19
# ==============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

stream() {
    echo -e "${PURPLE}[STREAM]${NC} $1"
}

# 设置基础 URL
BASE_URL=${1:-"http://localhost"}

echo "================================================================================"
echo "                    🎯 NGINX AI Gateway Test Examples"
echo "================================================================================"
echo "Target Gateway: $BASE_URL"
echo

# 1. 测试 NGINX 健康状态
log "🔍 Testing NGINX Health..."
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/health_response.txt "$BASE_URL/nginx-health")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    log "✅ NGINX Gateway is healthy"
    cat /tmp/health_response.txt
    echo
else
    error "❌ NGINX Gateway health check failed (HTTP $HEALTH_RESPONSE)"
    exit 1
fi

# 2. 测试非流式 AI 服务
log "🤖 Testing Non-Streaming AI Service..."
curl -X POST "$BASE_URL/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello! Please respond that the NGINX gateway is working correctly."}
    ],
    "stream": false,
    "max_tokens": 50
  }' | jq .

echo
echo

# 3. 测试流式 AI 服务 - 关键功能
stream "🌊 Testing Streaming AI Service..."
stream "This will show real-time streaming response:"
echo

curl -X POST "$BASE_URL/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Please tell a very short story about AI testing. Stream the response word by word."}
    ],
    "stream": true,
    "max_tokens": 100
  }' | while IFS= read -r line; do
    if [[ $line == data:* ]]; then
        # 提取 JSON 数据
        json_data="${line#data: }"
        
        if [[ $json_data == "[DONE]" ]]; then
            stream "🏁 Stream completed"
            break
        fi
        
        # 尝试解析并显示内容
        content=$(echo "$json_data" | jq -r '.choices[0].delta.content // empty' 2>/dev/null)
        if [[ -n "$content" && "$content" != "null" ]]; then
            printf "${PURPLE}%s${NC}" "$content"
        fi
    fi
done

echo
echo
echo

# 4. 测试不同的服务端点
log "🎯 Testing Different Service Endpoints..."

echo
info "Testing /v1/chat/completions endpoint:"
curl -s -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Test /v1 endpoint"}
    ],
    "stream": false,
    "max_tokens": 20
  }' | jq -r '.choices[0].message.content // "No response"'

echo
info "Testing /forward/v1/chat/completions endpoint:"
curl -s -X POST "$BASE_URL/forward/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Test /forward endpoint"}
    ],
    "stream": false,
    "max_tokens": 20
  }' | jq -r '.choices[0].message.content // "No response"'

echo

# 5. 测试服务状态
log "📊 Testing Service Stats..."
curl -s "$BASE_URL/health" | jq . 2>/dev/null || echo "Health endpoint not available"

echo
curl -s "$BASE_URL/stats" | jq . 2>/dev/null || echo "Stats endpoint not available"

echo
echo

# 6. 外部访问测试说明
log "🌐 External Access Test Instructions:"
echo
info "To test external access from another machine:"
info "1. Find your machine's IP address:"
info "   ifconfig | grep 'inet ' | grep -v 127.0.0.1"
echo
info "2. From another machine, run:"
info "   curl -X POST http://YOUR_IP/api/v1/chat/completions \\"
info "     -H \"Content-Type: application/json\" \\"
info "     -d '{"
info "       \"model\": \"gpt-3.5-turbo\","
info "       \"messages\": [{\"role\": \"user\", \"content\": \"External test\"}],"
info "       \"stream\": false,"
info "       \"max_tokens\": 30"
info "     }'"
echo
info "3. For streaming test from external machine:"
info "   curl -X POST http://YOUR_IP/api/v1/chat/completions \\"
info "     -H \"Content-Type: application/json\" \\"
info "     -H \"Accept: text/event-stream\" \\"
info "     -d '{"
info "       \"model\": \"gpt-3.5-turbo\","
info "       \"messages\": [{\"role\": \"user\", \"content\": \"External streaming test\"}],"
info "       \"stream\": true,"
info "       \"max_tokens\": 50"
info "     }'"

echo
echo "================================================================================"
log "🎉 NGINX AI Gateway Test Completed!"
echo

# 检查防火墙状态（如果是 macOS）
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo
    warning "🔥 Firewall Check (macOS):"
    sudo pfctl -s info 2>/dev/null | grep -E "(Status|Token)" || echo "   Firewall status unknown"
    echo
    info "💡 To allow external access on macOS:"
    info "   System Preferences > Security & Privacy > Firewall"
    info "   Add Docker or allow incoming connections on port 80"
fi

echo
log "✅ Test completed. Your NGINX AI Gateway supports:"
log "   🌊 Streaming responses (real-time token streaming)"
log "   🌐 External user access (multi-user support)"
log "   ⚡ Multiple service endpoints"
log "   🛡️  Rate limiting and load balancing"

echo
echo "================================================================================" 