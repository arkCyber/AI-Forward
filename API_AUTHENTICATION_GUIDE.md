# 🔐 Smart AI Router - API 身份验证指南

## 📋 身份验证概述

Smart AI Router 现在支持 **API 密钥身份验证**，确保只有授权用户可以访问统一AI API端点。

### 🔑 API 密钥配置

系统支持两种身份验证模式：

1. **共享密钥模式** (当前配置) - 所有用户使用同一个密钥
2. **多用户模式** - 每个用户有独立的密钥和配额

## 🚀 当前配置 - 共享密钥模式

### 统一API密钥
```
sk-8d6804b011614dba7bd065f8644514b
```

### 特点
- ✅ **简单易用**: 所有用户使用同一个密钥
- ✅ **无配额限制**: 999,999 次/天的超高限额
- ✅ **即时可用**: 无需注册或申请

## 🔧 如何使用

### 1. 基本请求格式

```bash
curl -X POST http://localhost:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-router-2024-unified-api-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "您的问题"}],
    "max_tokens": 100
  }'
```

### 2. Python 示例

```python
import httpx

# 配置API密钥
API_KEY = "sk-8d6804b011614dba7bd065f8644514b"
BASE_URL = "http://localhost:9000"

def chat_with_ai(message: str) -> str:
    """与AI聊天的函数"""
    client = httpx.Client()
    
    response = client.post(
        f"{BASE_URL}/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        },
        json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": message}],
            "max_tokens": 150
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # 响应中包含路由信息
        router_info = data.get("_router_info", {})
        print(f"Provider: {router_info.get('provider')}")
        print(f"Response Time: {router_info.get('response_time'):.2f}s")
        print(f"Requests Today: {router_info.get('requests_today')}/{router_info.get('daily_limit')}")
        
        return data["choices"][0]["message"]["content"]
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")

# 使用示例
try:
    response = chat_with_ai("解释什么是人工智能")
    print(f"AI回复: {response}")
except Exception as e:
    print(f"错误: {e}")
```

### 3. JavaScript 示例

```javascript
const API_KEY = "sk-8d6804b011614dba7bd065f8644514b";
const BASE_URL = "http://localhost:9000";

async function chatWithAI(message) {
    try {
        const response = await fetch(`${BASE_URL}/v1/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`
            },
            body: JSON.stringify({
                model: 'gpt-3.5-turbo',
                messages: [{ role: 'user', content: message }],
                max_tokens: 150
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }

        const data = await response.json();
        
        // 显示路由信息
        const routerInfo = data._router_info;
        console.log(`Provider: ${routerInfo.provider}`);
        console.log(`Response Time: ${routerInfo.response_time.toFixed(2)}s`);
        console.log(`Requests Today: ${routerInfo.requests_today}/${routerInfo.daily_limit}`);
        
        return data.choices[0].message.content;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// 使用示例
chatWithAI("写一个简单的Python函数")
    .then(response => console.log("AI回复:", response))
    .catch(error => console.error("错误:", error));
```

## 📊 API 端点详情

### 主要端点

| 端点 | 需要认证 | 描述 |
|------|----------|------|
| `POST /v1/chat/completions` | ✅ **是** | 聊天完成API |
| `GET /stats` | ✅ **是** | 使用统计信息 |
| `GET /health` | ❌ 否 | 健康检查 |
| `GET /auth/info` | ❌ 否 | 身份验证配置信息 |

### 响应中的身份验证信息

成功的API调用会在响应中包含用户信息：

```json
{
  "choices": [...],
  "_router_info": {
    "provider": "deepseek",
    "response_time": 4.26,
    "timestamp": "2025-06-03T21:17:04.502012",
    "user_id": "shared_user",
    "requests_today": 1,
    "daily_limit": 999999
  }
}
```

## ⚠️ 错误处理

### 常见错误和解决方案

1. **401 Unauthorized - "Not authenticated"**
   ```
   原因: 未提供Authorization头
   解决: 添加 'Authorization: Bearer YOUR_API_KEY' 头部
   ```

2. **401 Unauthorized - "Invalid API key"**
   ```
   原因: API密钥错误
   解决: 检查密钥是否正确: sk-8d6804b011614dba7bd065f8644514b
   ```

3. **403 Forbidden - "User account is inactive"**
   ```
   原因: 用户账户被禁用（多用户模式）
   解决: 联系管理员激活账户
   ```

4. **429 Too Many Requests - "Daily quota exceeded"**
   ```
   原因: 超过每日配额限制
   解决: 等待次日重置或联系管理员提高限额
   ```

## 🔄 切换到多用户模式

如果需要为不同用户分配独立的密钥和配额，可以修改 `ai_router.py` 中的配置：

```python
# 在 setup_authentication 方法中修改
self.auth_mode = "multi_user"  # 改为 "multi_user"
```

### 多用户模式预配置的密钥

```
sk-user-demo-key-001    # demo_user_001, 500次/天
sk-user-admin-key-999   # admin_user, 10000次/天
```

## 📈 监控使用情况

### 查看个人使用统计

```bash
curl -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" \
     http://localhost:9000/stats | python3 -m json.tool
```

响应包含：
- 总请求数
- 成功/失败统计
- 提供商使用情况
- 个人使用信息（今日请求数、限额等）

### 查看身份验证配置

```bash
curl http://localhost:9000/auth/info | python3 -m json.tool
```

## 🛡️ 安全最佳实践

1. **保护API密钥**
   - 不要在公开代码中硬编码API密钥
   - 使用环境变量存储密钥
   - 定期轮换密钥

2. **网络安全**
   - 生产环境使用HTTPS
   - 限制访问IP地址（如需要）
   - 监控异常请求模式

3. **配额管理**
   - 根据需要调整每日限额
   - 监控使用模式
   - 设置告警阈值

## 🎯 快速测试

### 测试身份验证
```bash
# 正确的密钥 - 应该成功
curl -X POST http://localhost:9000/v1/chat/completions \
  -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"Hello!"}]}'

# 错误的密钥 - 应该返回401
curl -X POST http://localhost:9000/v1/chat/completions \
  -H "Authorization: Bearer wrong-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"Hello!"}]}'

# 无密钥 - 应该返回401
curl -X POST http://localhost:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"Hello!"}]}'
```

## 📞 支持和维护

如需修改身份验证配置、添加新用户或调整配额，请：

1. 修改 `ai_router.py` 中的相关配置
2. 重新构建Docker镜像：`docker-compose build ai-router`
3. 重启服务：`./start_ai_router.sh restart`

现在您的 Smart AI Router 已经具备了完善的身份验证功能！🎉 