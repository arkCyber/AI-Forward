# 🔄 NGINX AI Gateway 访问方法对比

## 📋 概述

本文档详细对比使用 NGINX 反向代理前后的 API 访问方法变化，并提供完整的使用案例。

---

## ⚡ **使用 NGINX 前** - 直接访问

### 🎯 访问方式
```
直接访问 AI Router 服务：
- URL: http://localhost:9000/v1/chat/completions
- Port: 9000 (AI Router 端口)
- API Key: sk-8d6804b011614dba7bd065f8644514b
```

### 📝 使用案例

#### 非流式请求
```bash
curl -X POST http://localhost:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "stream": false,
    "max_tokens": 50
  }'
```

#### 流式请求
```bash
curl -N -X POST http://localhost:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" \
  -H "Accept: text/event-stream" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "请告诉我一个故事"}
    ],
    "stream": true,
    "max_tokens": 100
  }'
```

### ⚠️ 直接访问的限制
- ❌ 无负载均衡
- ❌ 无速率限制
- ❌ 无故障转移
- ❌ 单点故障风险
- ❌ 无外部访问优化

---

## 🚀 **使用 NGINX 后** - 统一网关

### 🎯 访问方式

NGINX 提供了**多种访问端点**，满足不同需求：

#### 1. **主要 API 端点** (🌟 **推荐使用**)
```
URL: http://localhost/api/v1/chat/completions
Port: 80 (NGINX 网关端口)
特性: 负载均衡 + 速率限制 + 故障转移
```

#### 2. **直接 v1 端点** (兼容原有接口)
```
URL: http://localhost/v1/chat/completions
Port: 80 (NGINX 网关端口)
特性: 与原 9000 端口接口保持兼容
```

#### 3. **特定服务端点**
```
DeepSeek:     http://localhost/deepseek/v1/chat/completions
LingyiWanwu:  http://localhost/lingyiwanwu/v1/chat/completions
Ollama:       http://localhost/ollama/v1/chat/completions
```

### 📝 详细使用案例

#### 🌟 **方案一：主要 API 端点** (生产环境推荐)

**非流式请求：**
```bash
curl -X POST http://localhost/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "使用NGINX网关测试"}
    ],
    "stream": false,
    "max_tokens": 50
  }'
```

**流式请求：**
```bash
curl -N -X POST http://localhost/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" \
  -H "Accept: text/event-stream" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "请用流式输出讲一个AI的故事"}
    ],
    "stream": true,
    "max_tokens": 150
  }'
```

#### 🔄 **方案二：兼容端点** (保持原有习惯)

将原来的 `localhost:9000/v1` 改为 `localhost/v1`：

**非流式请求：**
```bash
curl -X POST http://localhost/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "兼容性测试"}
    ],
    "stream": false,
    "max_tokens": 30
  }'
```

**流式请求：**
```bash
curl -N -X POST http://localhost/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" \
  -H "Accept: text/event-stream" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "流式兼容性测试"}
    ],
    "stream": true,
    "max_tokens": 80
  }'
```

#### 🎯 **方案三：特定服务** (指定 AI 提供商)

**DeepSeek 服务：**
```bash
curl -X POST http://localhost/deepseek/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" \
  -d '{
    "model": "deepseek-chat",
    "messages": [
      {"role": "user", "content": "DeepSeek AI 测试"}
    ],
    "stream": false,
    "max_tokens": 40
  }'
```

**Ollama 本地模型：**
```bash
curl -X POST http://localhost/ollama/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" \
  -d '{
    "model": "llama3.2",
    "messages": [
      {"role": "user", "content": "Ollama 本地模型测试"}
    ],
    "stream": false,
    "max_tokens": 50
  }'
```

### 🌐 **外部访问** (多用户环境)

如果需要外部用户访问，将 `localhost` 替换为您的机器 IP：

#### 外部非流式请求：
```bash
curl -X POST http://192.168.252.25/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "外部用户访问测试"}
    ],
    "stream": false,
    "max_tokens": 50
  }'
```

#### 外部流式请求：
```bash
curl -N -X POST http://192.168.252.25/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" \
  -H "Accept: text/event-stream" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "外部流式访问测试"}
    ],
    "stream": true,
    "max_tokens": 100
  }'
```

---

## 📊 **对比总结**

| 特性 | 使用 NGINX 前 | 使用 NGINX 后 |
|------|---------------|---------------|
| **访问地址** | `localhost:9000/v1` | `localhost/api/v1` (推荐) |
| **端口** | 9000 | 80 |
| **负载均衡** | ❌ 无 | ✅ 有 |
| **速率限制** | ❌ 无 | ✅ 有 (100/min) |
| **故障转移** | ❌ 无 | ✅ 有 |
| **外部访问** | ⚠️ 需要暴露 9000 端口 | ✅ 标准 80 端口 |
| **SSL 支持** | ❌ 无 | ✅ 就绪 (443 端口) |
| **多服务支持** | ❌ 单一路由 | ✅ 多端点路由 |
| **监控能力** | ❌ 基础 | ✅ 详细统计 |

---

## 🎯 **迁移建议**

### 1. **无缝迁移** (推荐)
将现有代码中的：
```
http://localhost:9000/v1/chat/completions
```
改为：
```
http://localhost/v1/chat/completions
```

### 2. **优化升级** (生产环境)
使用新的主要端点：
```
http://localhost/api/v1/chat/completions
```

### 3. **分布式部署**
使用机器 IP 地址：
```
http://YOUR_IP/api/v1/chat/completions
```

---

## 🔧 **代码示例** (Python)

### 迁移前
```python
import requests

url = "http://localhost:9000/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer sk-8d6804b011614dba7bd065f8644514b"
}
data = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": False
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### 迁移后 (兼容方式)
```python
import requests

# 只需要修改这一行
url = "http://localhost/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer sk-8d6804b011614dba7bd065f8644514b"
}
data = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": False
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### 推荐方式 (生产环境)
```python
import requests

# 使用推荐的 API 端点
url = "http://localhost/api/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer sk-8d6804b011614dba7bd065f8644514b"
}
data = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": False
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

---

## ✅ **总结**

**使用 NGINX 后的优势：**
- 🚀 **性能提升**：负载均衡和连接复用
- 🛡️ **安全增强**：速率限制和访问控制
- 🌐 **外部友好**：标准端口和 SSL 就绪
- 📊 **监控完善**：详细的服务统计
- 🔄 **高可用性**：故障转移和健康检查

**推荐的迁移路径：**
1. 使用 `/v1` 端点进行兼容性迁移
2. 逐步升级到 `/api/v1` 端点
3. 启用外部访问和 SSL 配置

您的 AI 网关现在通过 NGINX 提供了**企业级的服务能力**！🎉 