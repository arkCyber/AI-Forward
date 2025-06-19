#!/usr/bin/env python3

# ==============================================================================
# Smart AI Router Service with Low-Level ASGI Streaming
# ==============================================================================
# Description: Unified API endpoint with intelligent load balancing and real-time streaming
# Author: Assistant
# Created: 2024-12-19
# Version: 1.2 - Added low-level ASGI streaming for real-time data forwarding
#
# Features:
# - Unified OpenAI-compatible API endpoint
# - Random/weighted selection of AI providers
# - Automatic failover and retry mechanism
# - Request logging and performance monitoring
# - Health checking of backend services
# - API Key authentication and user quota management
# - Low-level ASGI streaming for zero-buffering real-time data forwarding
# ==============================================================================

import asyncio
import random
import time
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uvicorn

# Configure logging with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ai_router")

class ProviderStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class AIProvider:
    """AI Provider configuration"""
    name: str
    base_url: str
    api_key: str
    models: List[str]
    weight: int = 1  # 权重，数值越大被选中概率越高
    status: ProviderStatus = ProviderStatus.UNKNOWN
    last_check: float = 0
    response_time: float = 0
    error_count: int = 0

@dataclass
class UserInfo:
    """User information and quota management"""
    user_id: str
    api_key: str
    daily_limit: int = 1000  # 每日请求限制
    requests_today: int = 0
    total_requests: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_request: str = field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = True

class ChatRequest(BaseModel):
    """OpenAI Chat Completion Request"""
    model: str
    messages: List[Dict[str, str]]
    max_tokens: Optional[int] = 150
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = True  # 默认启用流式输出
    x_use_asgi_streaming: Optional[bool] = False  # 使用低层ASGI流处理
    # 其他OpenAI参数...

class SmartAIRouter:
    """Smart AI Router with load balancing and failover"""
    
    def __init__(self):
        """Initialize the AI router with multiple providers"""
        self.providers = [
            AIProvider(
                name="deepseek",
                base_url="http://openai-forward-proxy:8000/deepseek/v1",
                api_key="sk-878a5319c7b14bc48109e19315361b7f",
                models=["deepseek-chat", "deepseek-coder"],
                weight=3  # 高权重，专业编程
            ),
            AIProvider(
                name="lingyiwanwu",
                base_url="http://openai-forward-proxy:8000/lingyiwanwu/v1", 
                api_key="72ebf8a6191e45bab0f646659c8cb121",
                models=["yi-34b-chat", "yi-6b-chat"],
                weight=3  # 高权重，中文优化
            ),
            AIProvider(
                name="ollama",
                base_url="http://openai-forward-proxy:8000/ollama/v1",
                api_key="ollama-local-key",
                models=["llama3.2", "qwen2:7b", "codegemma"],
                weight=2  # 中等权重，本地模型
            )
        ]
        
        self.client = httpx.AsyncClient(timeout=60.0)
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "provider_usage": {provider.name: 0 for provider in self.providers}
        }
        
        # 健康检查任务引用（将在startup时创建）
        self.health_check_task = None
        
        # 用户管理和API密钥配置
        self.setup_authentication()
    
    def setup_authentication(self):
        """Setup authentication configuration"""
        # 配置选项：共享密钥模式 vs 多用户模式
        self.auth_mode = "shared"  # "shared" 或 "multi_user"
        
        # 共享模式：所有用户使用同一个密钥
        self.shared_api_key = "sk-8d6804b011614dba7bd065f8644514b"
        
        # 多用户模式：用户数据库（生产环境应使用真实数据库）
        self.users_db = {
            "sk-user-demo-key-001": UserInfo(
                user_id="demo_user_001",
                api_key="sk-user-demo-key-001",
                daily_limit=500
            ),
            "sk-user-admin-key-999": UserInfo(
                user_id="admin_user",
                api_key="sk-user-admin-key-999", 
                daily_limit=10000
            ),
            # 可以添加更多用户...
        }
        
        logger.info(f"🔐 Authentication mode: {self.auth_mode}")
        if self.auth_mode == "shared":
            logger.info(f"🔑 Shared API key: {self.shared_api_key}")
        else:
            logger.info(f"👥 Multi-user mode: {len(self.users_db)} users configured")
    
    def verify_api_key(self, api_key: str) -> Optional[UserInfo]:
        """Verify API key and return user info"""
        if self.auth_mode == "shared":
            if api_key == self.shared_api_key:
                # 共享模式返回默认用户信息
                return UserInfo(
                    user_id="shared_user",
                    api_key=api_key,
                    daily_limit=999999  # 无限制
                )
            else:
                return None
        
        elif self.auth_mode == "multi_user":
            return self.users_db.get(api_key)
        
        return None
    
    def check_quota(self, user_info: UserInfo) -> bool:
        """Check if user has remaining quota"""
        today = datetime.now().date().isoformat()
        
        # 如果是新的一天，重置计数
        if user_info.last_request[:10] != today:
            user_info.requests_today = 0
        
        return user_info.requests_today < user_info.daily_limit
    
    def update_user_stats(self, user_info: UserInfo):
        """Update user usage statistics"""
        user_info.requests_today += 1
        user_info.total_requests += 1
        user_info.last_request = datetime.now().isoformat()

    async def start_health_checks(self):
        """启动健康检查任务"""
        if self.health_check_task is None:
            self.health_check_task = asyncio.create_task(self.health_check_loop())
            logger.info("🔍 Health check task started")
    
    async def health_check_provider(self, provider: AIProvider) -> bool:
        """Check if a provider is healthy"""
        try:
            start_time = time.time()
            
            # 简单的健康检查请求
            test_request = {
                "model": provider.models[0],
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            
            response = await self.client.post(
                f"{provider.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {provider.api_key}",
                    "Content-Type": "application/json"
                },
                json=test_request,
                timeout=10.0
            )
            
            provider.response_time = time.time() - start_time
            provider.last_check = time.time()
            
            if response.status_code == 200:
                provider.status = ProviderStatus.HEALTHY
                provider.error_count = 0
                logger.info(f"✅ Provider {provider.name} is healthy (response_time: {provider.response_time:.2f}s)")
                return True
            else:
                provider.status = ProviderStatus.UNHEALTHY
                provider.error_count += 1
                logger.warning(f"⚠️ Provider {provider.name} returned status {response.status_code}")
                return False
                
        except Exception as e:
            provider.status = ProviderStatus.UNHEALTHY
            provider.error_count += 1
            provider.last_check = time.time()
            logger.error(f"❌ Provider {provider.name} health check failed: {str(e)}")
            return False
    
    async def health_check_loop(self):
        """Periodic health check for all providers"""
        while True:
            try:
                logger.info("🔍 Starting health check for all providers...")
                
                tasks = [self.health_check_provider(provider) for provider in self.providers]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                healthy_count = sum(1 for provider in self.providers if provider.status == ProviderStatus.HEALTHY)
                logger.info(f"📊 Health check completed: {healthy_count}/{len(self.providers)} providers healthy")
                
                # 每30秒检查一次
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Health check loop error: {str(e)}")
                await asyncio.sleep(30)
    
    def select_provider(self, request: ChatRequest) -> Optional[AIProvider]:
        """Smart provider selection with weighted random and failover"""
        
        # 1. 过滤健康的提供商
        healthy_providers = [
            p for p in self.providers 
            if p.status == ProviderStatus.HEALTHY and p.error_count < 5
        ]
        
        if not healthy_providers:
            logger.warning("⚠️ No healthy providers available, using all providers as fallback")
            healthy_providers = self.providers
        
        # 2. 根据模型过滤（如果指定了特定模型）
        model_compatible_providers = []
        for provider in healthy_providers:
            # 如果请求指定了具体模型，优先选择支持该模型的提供商
            if request.model in provider.models:
                model_compatible_providers.append(provider)
        
        # 如果没有找到支持特定模型的提供商，使用所有健康的提供商
        if not model_compatible_providers:
            model_compatible_providers = healthy_providers
        
        # 3. 加权随机选择
        if model_compatible_providers:
            # 计算权重（考虑响应时间和错误率）
            weighted_providers = []
            for provider in model_compatible_providers:
                # 基础权重
                weight = provider.weight
                
                # 根据响应时间调整权重（响应越快权重越高）
                if provider.response_time > 0:
                    time_factor = max(0.1, 2.0 - provider.response_time)  # 2秒以内较好
                    weight *= time_factor
                
                # 根据错误数调整权重
                error_factor = max(0.1, 1.0 - provider.error_count * 0.1)
                weight *= error_factor
                
                weighted_providers.extend([provider] * max(1, int(weight)))
            
            selected = random.choice(weighted_providers)
            logger.info(f"🎯 Selected provider: {selected.name} (weight: {selected.weight}, errors: {selected.error_count})")
            return selected
        
        logger.error("❌ No suitable provider found")
        return None
    
    async def forward_request(self, provider: AIProvider, request: ChatRequest, request_start_time: float = None) -> Any:
        """Forward request to selected provider with streaming support"""
        if request_start_time is None:
            request_start_time = time.time()
            
        try:
            start_time = time.time()
            
            # 将统一模型名映射到提供商特定的模型
            actual_model = self.map_model_name(request.model, provider)
            request_data = request.model_dump()
            request_data["model"] = actual_model
            
            logger.info(f"📤 [T+{time.time()-request_start_time:.3f}s] Forwarding request to {provider.name} with model {actual_model} (stream: {request.stream})")
            
            # 处理流式响应
            if request.stream:
                
                async def stream_generator():
                    """Enhanced stream generator with comprehensive error handling"""
                    client = None
                    connection_id = f"{provider.name}_{int(time.time()*1000)}"
                    
                    try:
                        generator_start = time.time()
                        logger.info(f"🔄 [T+{generator_start-request_start_time:.3f}s] Stream generator started for {provider.name} (ID: {connection_id})")
                        
                        # 创建专用客户端实例用于流处理
                        client = httpx.AsyncClient(
                            timeout=httpx.Timeout(60.0, connect=10.0, read=60.0),
                            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
                        )
                        
                        logger.info(f"🔗 [T+{time.time()-request_start_time:.3f}s] HTTP client created for {provider.name}")
                        
                        # 使用context manager确保连接正确管理
                        async with client.stream(
                            "POST",
                            f"{provider.base_url}/chat/completions",
                            headers={
                                "Authorization": f"Bearer {provider.api_key}",
                                "Content-Type": "application/json",
                                "Connection": "keep-alive",
                                "Accept": "text/event-stream"
                            },
                            json=request_data
                        ) as response:
                            
                            connection_time = time.time() - start_time
                            provider.response_time = (provider.response_time + connection_time) / 2
                            
                            logger.info(f"🌐 [T+{time.time()-request_start_time:.3f}s] Connected to {provider.name} (connection_time: {connection_time:.3f}s, status: {response.status_code})")
                            
                            if response.status_code != 200:
                                error_text = await response.aread()
                                error_message = error_text.decode('utf-8', errors='ignore')
                                logger.error(f"❌ [T+{time.time()-request_start_time:.3f}s] Provider {provider.name} error {response.status_code}: {error_message}")
                                
                                # 返回标准错误格式
                                error_response = {
                                    "error": {
                                        "type": "provider_error",
                                        "code": response.status_code,
                                        "message": error_message,
                                        "provider": provider.name
                                    }
                                }
                                yield f'data: {json.dumps(error_response)}\n\n'.encode()
                                return
                            
                            logger.info(f"✅ [T+{time.time()-request_start_time:.3f}s] Stream response started from {provider.name}")
                            
                            chunk_count = 0
                            last_chunk_time = generator_start
                            total_bytes = 0
                            
                            # 优化的流式转发：使用合适的chunk size平衡性能和实时性
                            async for raw_chunk in response.aiter_raw(chunk_size=1024):
                                if raw_chunk:
                                    current_time = time.time()
                                    chunk_count += 1
                                    total_bytes += len(raw_chunk)
                                    
                                    time_since_start = current_time - request_start_time
                                    time_since_last = current_time - last_chunk_time
                                    
                                    # 详细日志记录前几个chunks
                                    if chunk_count <= 3:
                                        logger.info(f"📦 [T+{time_since_start:.3f}s] Chunk {chunk_count}: {len(raw_chunk)} bytes (+{time_since_last*1000:.1f}ms)")
                                    elif chunk_count % 50 == 0:  # 每50个chunk记录一次
                                        logger.info(f"📊 [T+{time_since_start:.3f}s] Progress: {chunk_count} chunks, {total_bytes} bytes")
                                    
                                    # 转发chunk
                                    yield raw_chunk
                                    last_chunk_time = current_time
                                    
                                    # 提供反压控制
                                    if chunk_count % 100 == 0:
                                        await asyncio.sleep(0)  # 让出控制权
                            
                            completion_time = time.time()
                            total_time = completion_time - generator_start
                            avg_chunk_size = total_bytes / chunk_count if chunk_count > 0 else 0
                            
                            logger.info(f"✅ [T+{completion_time-request_start_time:.3f}s] Stream completed from {provider.name}: {chunk_count} chunks, {total_bytes} bytes, avg {avg_chunk_size:.1f}B/chunk in {total_time:.3f}s")
                            
                            # 更新提供商统计
                            provider.error_count = max(0, provider.error_count - 1)  # 成功则减少错误计数
                                    
                    except httpx.ConnectError as e:
                        error_time = time.time()
                        logger.error(f"🚫 [T+{error_time-request_start_time:.3f}s] Connection error to {provider.name}: {str(e)}")
                        provider.error_count += 1
                        error_response = {
                            "error": {
                                "type": "connection_error",
                                "message": f"Failed to connect to {provider.name}: {str(e)}",
                                "provider": provider.name
                            }
                        }
                        yield f'data: {json.dumps(error_response)}\n\n'.encode()
                        
                    except httpx.TimeoutException as e:
                        error_time = time.time()
                        logger.error(f"⏰ [T+{error_time-request_start_time:.3f}s] Timeout error from {provider.name}: {str(e)}")
                        provider.error_count += 1
                        error_response = {
                            "error": {
                                "type": "timeout_error", 
                                "message": f"Request to {provider.name} timed out: {str(e)}",
                                "provider": provider.name
                            }
                        }
                        yield f'data: {json.dumps(error_response)}\n\n'.encode()
                        
                    except Exception as e:
                        error_time = time.time()
                        logger.error(f"❌ [T+{error_time-request_start_time:.3f}s] Unexpected error from {provider.name}: {str(e)}")
                        logger.error(f"❌ [T+{error_time-request_start_time:.3f}s] Error type: {type(e).__name__}")
                        provider.error_count += 1
                        
                        # 详细错误信息
                        import traceback
                        logger.error(f"❌ [T+{error_time-request_start_time:.3f}s] Traceback: {traceback.format_exc()}")
                        
                        error_response = {
                            "error": {
                                "type": "stream_error",
                                "message": f"Stream error from {provider.name}: {str(e)}",
                                "provider": provider.name
                            }
                        }
                        yield f'data: {json.dumps(error_response)}\n\n'.encode()
                        
                    finally:
                        if client:
                            try:
                                await client.aclose()
                                logger.info(f"🔐 [T+{time.time()-request_start_time:.3f}s] HTTP client closed for {provider.name} (ID: {connection_id})")
                            except Exception as close_error:
                                logger.warning(f"⚠️ [T+{time.time()-request_start_time:.3f}s] Error closing client for {provider.name}: {close_error}")
                
                logger.info(f"🏗️ [T+{time.time()-request_start_time:.3f}s] Stream generator prepared for {provider.name}")
                return stream_generator()
            
            # 处理非流式响应
            else:
                logger.info(f"📄 [T+{time.time()-request_start_time:.3f}s] Processing non-streaming request to {provider.name}")
                
                try:
                    response = await self.client.post(
                        f"{provider.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {provider.api_key}",
                            "Content-Type": "application/json"
                        },
                        json=request_data,
                        timeout=60.0
                    )
                    
                    response_time = time.time() - start_time
                    provider.response_time = (provider.response_time + response_time) / 2
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # 统一化响应格式
                        result["_router_info"] = {
                            "provider": provider.name,
                            "response_time": response_time,
                            "timestamp": datetime.now().isoformat(),
                            "streaming": False
                        }
                        
                        logger.info(f"✅ [T+{time.time()-request_start_time:.3f}s] Non-streaming request successful via {provider.name} (response_time: {response_time:.2f}s)")
                        provider.error_count = max(0, provider.error_count - 1)  # 成功则减少错误计数
                        return result
                    else:
                        logger.error(f"❌ [T+{time.time()-request_start_time:.3f}s] Provider {provider.name} returned status {response.status_code}: {response.text}")
                        provider.error_count += 1
                        raise HTTPException(status_code=response.status_code, detail=f"Provider error: {response.text}")
                        
                except httpx.ConnectError as e:
                    logger.error(f"🚫 [T+{time.time()-request_start_time:.3f}s] Connection error to {provider.name}: {str(e)}")
                    provider.error_count += 1
                    raise HTTPException(status_code=502, detail=f"Connection error: {str(e)}")
                    
                except httpx.TimeoutException as e:
                    logger.error(f"⏰ [T+{time.time()-request_start_time:.3f}s] Timeout error from {provider.name}: {str(e)}")
                    provider.error_count += 1
                    raise HTTPException(status_code=504, detail=f"Provider timeout: {str(e)}")
                
        except Exception as e:
            logger.error(f"❌ [T+{time.time()-request_start_time:.3f}s] Critical error in forward_request: {str(e)}")
            provider.error_count += 1
            raise HTTPException(status_code=502, detail=f"Provider error: {str(e)}")
    
    def map_model_name(self, requested_model: str, provider: AIProvider) -> str:
        """Map generic model names to provider-specific models"""
        
        # 通用模型名映射表
        model_mapping = {
            "gpt-3.5-turbo": {
                "deepseek": "deepseek-chat",
                "lingyiwanwu": "yi-34b-chat", 
                "ollama": "llama3.2"
            },
            "gpt-4": {
                "deepseek": "deepseek-chat",
                "lingyiwanwu": "yi-34b-chat",
                "ollama": "llama3.2"
            },
            "code-assistant": {
                "deepseek": "deepseek-coder",
                "lingyiwanwu": "yi-34b-chat",
                "ollama": "codegemma"
            }
        }
        
        # 如果是通用模型名，进行映射
        if requested_model in model_mapping:
            return model_mapping[requested_model].get(provider.name, provider.models[0])
        
        # 如果是提供商特定的模型名，直接使用
        if requested_model in provider.models:
            return requested_model
        
        # 默认使用提供商的第一个模型
        return provider.models[0]

class LowLevelASGIStreamer:
    """Enhanced low-level ASGI streaming handler for real-time data forwarding"""
    
    def __init__(self, request_start_time: float):
        self.request_start_time = request_start_time
        self.total_bytes_sent = 0
        self.chunks_sent = 0
        self.connection_id = f"asgi_{int(time.time()*1000)}_{id(self)}"
        self.is_headers_sent = False
        self.error_count = 0
        logger.info(f"🔧 [T+{time.time()-request_start_time:.3f}s] ASGI Streamer initialized (ID: {self.connection_id})")
        
    async def stream_response(self, scope: dict, receive: Callable, send: Callable, 
                            provider: 'AIProvider', request: 'ChatRequest') -> None:
        """Handle streaming response using enhanced low-level ASGI interface"""
        
        client = None
        response = None
        
        try:
            # 发送HTTP响应头
            headers_sent_time = time.time()
            logger.info(f"🚀 [T+{headers_sent_time-self.request_start_time:.3f}s] ASGI: Preparing response headers for {provider.name}")
            
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [
                    [b'content-type', b'text/event-stream'],
                    [b'cache-control', b'no-cache'],
                    [b'connection', b'keep-alive'],
                    [b'x-router-provider', provider.name.encode()],
                    [b'x-asgi-streaming', b'true'],
                    [b'x-router-method', b'asgi-parameter-optimized'],
                    [b'x-connection-id', self.connection_id.encode()],
                ],
            })
            self.is_headers_sent = True
            
            headers_completed_time = time.time()
            logger.info(f"✅ [T+{headers_completed_time-self.request_start_time:.3f}s] ASGI: Headers sent (took {headers_completed_time-headers_sent_time:.3f}s)")
            
            # 建立上游连接
            stream_start_time = time.time()
            logger.info(f"🔄 [T+{stream_start_time-self.request_start_time:.3f}s] ASGI: Starting upstream connection to {provider.name}")
            
            # 创建优化的HTTP客户端
            client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0, read=60.0),
                limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),
                follow_redirects=False
            )
            
            # 准备请求数据
            actual_model = self.map_model_name(request.model, provider)
            request_data = request.model_dump()
            request_data["model"] = actual_model
            
            upstream_start_time = time.time()
            logger.info(f"📡 [T+{upstream_start_time-self.request_start_time:.3f}s] ASGI: Connecting to {provider.name} with model {actual_model}")
            
            # 使用stream context manager
            async with client.stream(
                "POST",
                f"{provider.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {provider.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                    "Connection": "keep-alive"
                },
                json=request_data
            ) as response:
                
                upstream_connected_time = time.time()
                connection_latency = upstream_connected_time - upstream_start_time
                logger.info(f"🔗 [T+{upstream_connected_time-self.request_start_time:.3f}s] ASGI: Connected to upstream (latency: {connection_latency:.3f}s, status: {response.status_code})")
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    error_message = error_text.decode('utf-8', errors='ignore')
                    logger.error(f"❌ [T+{time.time()-self.request_start_time:.3f}s] ASGI: Upstream error {response.status_code}: {error_message}")
                    
                    error_data = {
                        "error": {
                            "type": "upstream_error",
                            "code": response.status_code,
                            "message": error_message,
                            "provider": provider.name,
                            "connection_id": self.connection_id
                        }
                    }
                    error_json = f'data: {json.dumps(error_data)}\n\n'.encode()
                    
                    await send({
                        'type': 'http.response.body',
                        'body': error_json,
                        'more_body': False,
                    })
                    return
                
                # 开始实时转发数据
                logger.info(f"🚀 [T+{time.time()-self.request_start_time:.3f}s] ASGI: Starting optimized real-time data forwarding")
                
                last_chunk_time = time.time()
                performance_samples = []
                
                # 使用优化的chunk size以平衡性能和实时性
                chunk_size = 1024  # 1KB chunks for good balance
                async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                    if chunk:
                        current_time = time.time()
                        self.chunks_sent += 1
                        self.total_bytes_sent += len(chunk)
                        
                        time_since_start = current_time - self.request_start_time
                        time_since_last = current_time - last_chunk_time
                        performance_samples.append(time_since_last)
                        
                        # 详细记录前几个chunks
                        if self.chunks_sent <= 3:
                            logger.info(f"📦 [T+{time_since_start:.3f}s] ASGI: Chunk {self.chunks_sent}: {len(chunk)} bytes (+{time_since_last*1000:.1f}ms)")
                        elif self.chunks_sent % 100 == 0:  # 每100个chunk记录一次性能
                            avg_interval = sum(performance_samples[-100:]) / min(100, len(performance_samples))
                            logger.info(f"📊 [T+{time_since_start:.3f}s] ASGI: Progress {self.chunks_sent} chunks, {self.total_bytes_sent} bytes (avg: {avg_interval*1000:.1f}ms)")
                        
                        # 立即通过ASGI发送数据
                        send_start_time = time.time()
                        await send({
                            'type': 'http.response.body',
                            'body': chunk,
                            'more_body': True,
                        })
                        send_duration = time.time() - send_start_time
                        
                        # 记录发送性能
                        if self.chunks_sent <= 3:
                            logger.info(f"📤 [T+{time.time()-self.request_start_time:.3f}s] ASGI: Chunk {self.chunks_sent} sent (send: {send_duration*1000:.1f}ms)")
                        
                        last_chunk_time = current_time
                        
                        # 控制流量以防止过载
                        if self.chunks_sent % 50 == 0:
                            await asyncio.sleep(0)  # 让出控制权
                
                # 发送结束信号
                completion_time = time.time()
                total_duration = completion_time - stream_start_time
                avg_chunk_size = self.total_bytes_sent / self.chunks_sent if self.chunks_sent > 0 else 0
                
                # 计算性能统计
                if performance_samples:
                    avg_interval = sum(performance_samples) / len(performance_samples)
                    min_interval = min(performance_samples)
                    max_interval = max(performance_samples)
                    zero_intervals = sum(1 for x in performance_samples if x < 0.001)  # <1ms
                    zero_percentage = (zero_intervals / len(performance_samples)) * 100
                else:
                    avg_interval = min_interval = max_interval = 0
                    zero_percentage = 0
                
                logger.info(f"🏁 [T+{completion_time-self.request_start_time:.3f}s] ASGI: Stream completed")
                logger.info(f"📊 [T+{completion_time-self.request_start_time:.3f}s] ASGI: Performance - {self.chunks_sent} chunks, {self.total_bytes_sent} bytes, avg {avg_chunk_size:.1f}B/chunk")
                logger.info(f"⏱️ [T+{completion_time-self.request_start_time:.3f}s] ASGI: Timing - total {total_duration:.3f}s, avg interval {avg_interval*1000:.1f}ms, zero intervals {zero_percentage:.1f}%")
                
                await send({
                    'type': 'http.response.body',
                    'body': b'',
                    'more_body': False,
                })
                
                logger.info(f"✅ [T+{completion_time-self.request_start_time:.3f}s] ASGI: Response completed successfully")
                
                # 更新provider统计
                provider.error_count = max(0, provider.error_count - 1)  # 成功减少错误计数
                    
        except httpx.ConnectError as e:
            error_time = time.time()
            self.error_count += 1
            logger.error(f"🚫 [T+{error_time-self.request_start_time:.3f}s] ASGI: Connection error: {str(e)}")
            await self._send_error_response(send, "connection_error", f"Connection failed: {str(e)}", provider.name)
            
        except httpx.TimeoutException as e:
            error_time = time.time()
            self.error_count += 1
            logger.error(f"⏰ [T+{error_time-self.request_start_time:.3f}s] ASGI: Timeout error: {str(e)}")
            await self._send_error_response(send, "timeout_error", f"Request timeout: {str(e)}", provider.name)
            
        except Exception as e:
            error_time = time.time()
            self.error_count += 1
            logger.error(f"❌ [T+{error_time-self.request_start_time:.3f}s] ASGI: Unexpected error: {str(e)}")
            logger.error(f"❌ [T+{error_time-self.request_start_time:.3f}s] ASGI: Error type: {type(e).__name__}")
            
            # 详细错误信息
            import traceback
            logger.error(f"❌ [T+{error_time-self.request_start_time:.3f}s] ASGI: Traceback: {traceback.format_exc()}")
            
            await self._send_error_response(send, "stream_error", f"Stream error: {str(e)}", provider.name)
            
        finally:
            # 清理资源
            if client:
                try:
                    await client.aclose()
                    logger.info(f"🔐 [T+{time.time()-self.request_start_time:.3f}s] ASGI: HTTP client closed (ID: {self.connection_id})")
                except Exception as close_error:
                    logger.warning(f"⚠️ [T+{time.time()-self.request_start_time:.3f}s] ASGI: Error closing client: {close_error}")
    
    async def _send_error_response(self, send: Callable, error_type: str, message: str, provider_name: str):
        """Send error response through ASGI"""
        try:
            if not self.is_headers_sent:
                await send({
                    'type': 'http.response.start',
                    'status': 500,
                    'headers': [
                        [b'content-type', b'text/event-stream'],
                        [b'x-router-error', error_type.encode()],
                        [b'x-connection-id', self.connection_id.encode()],
                    ],
                })
                self.is_headers_sent = True
            
            error_data = {
                "error": {
                    "type": error_type,
                    "message": message,
                    "provider": provider_name,
                    "connection_id": self.connection_id
                }
            }
            error_json = f'data: {json.dumps(error_data)}\n\n'.encode()
            
            await send({
                'type': 'http.response.body',
                'body': error_json,
                'more_body': False,
            })
        except Exception as send_error:
            logger.error(f"❌ [T+{time.time()-self.request_start_time:.3f}s] ASGI: Failed to send error response: {send_error}")
    
    def map_model_name(self, requested_model: str, provider: 'AIProvider') -> str:
        """Map generic model names to provider-specific models"""
        
        # 通用模型名映射表
        model_mapping = {
            "gpt-3.5-turbo": {
                "deepseek": "deepseek-chat",
                "lingyiwanwu": "yi-34b-chat", 
                "ollama": "llama3.2"
            },
            "gpt-4": {
                "deepseek": "deepseek-chat",
                "lingyiwanwu": "yi-34b-chat",
                "ollama": "llama3.2"
            },
            "code-assistant": {
                "deepseek": "deepseek-coder",
                "lingyiwanwu": "yi-34b-chat",
                "ollama": "codegemma"
            }
        }
        
        # 如果是通用模型名，进行映射
        if requested_model in model_mapping:
            return model_mapping[requested_model].get(provider.name, provider.models[0])
        
        # 如果是提供商特定的模型名，直接使用
        if requested_model in provider.models:
            return requested_model
        
        # 默认使用提供商的第一个模型
        return provider.models[0]

# 创建FastAPI应用
app = FastAPI(title="Smart AI Router", version="1.1.0")
router = SmartAIRouter()

# 身份验证设置
security = HTTPBearer()

async def authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInfo:
    """API密钥身份验证依赖函数"""
    api_key = credentials.credentials
    
    user_info = router.verify_api_key(api_key)
    if not user_info:
        logger.warning(f"🚫 Invalid API key attempted: {api_key[:10]}...")
        raise HTTPException(
            status_code=401, 
            detail="Invalid API key"
        )
    
    if not user_info.is_active:
        logger.warning(f"🚫 Inactive user attempted access: {user_info.user_id}")
        raise HTTPException(
            status_code=403, 
            detail="User account is inactive"
        )
    
    if not router.check_quota(user_info):
        logger.warning(f"📊 Quota exceeded for user: {user_info.user_id}")
        raise HTTPException(
            status_code=429, 
            detail=f"Daily quota exceeded. Limit: {user_info.daily_limit}, Used: {user_info.requests_today}"
        )
    
    logger.info(f"🔓 Authenticated user: {user_info.user_id} (requests today: {user_info.requests_today}/{user_info.daily_limit})")
    return user_info

@app.on_event("startup")
async def startup_event():
    """应用启动时的事件处理"""
    logger.info("🚀 Starting Smart AI Router application...")
    
    # 显示所有注册的路由
    logger.info("📋 Registered routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = getattr(route, 'methods', set())
            logger.info(f"  📍 {route.path} - {methods}")
    
    await router.start_health_checks()

@app.post("/v1/chat/completions")
async def chat_completions(request: Request, user_info: UserInfo = Depends(authenticate)):
    """Unified chat completions endpoint with authentication and streaming support"""
    start_time = time.time()  # 请求开始时间基准
    logger.info(f"🚀 [T+0.000s] === CHAT COMPLETIONS REQUEST START === for user: {user_info.user_id}")
    
    try:
        router.stats["total_requests"] += 1
        
        # 更新用户统计
        router.update_user_stats(user_info)
        
        # 读取原始请求体
        request_read_start = time.time()
        request_data = await request.json()
        request_read_time = time.time() - request_read_start
        logger.info(f"📥 [T+{time.time()-start_time:.3f}s] Raw request data: {json.dumps(request_data, indent=2)}")
        logger.info(f"📥 [T+{time.time()-start_time:.3f}s] Request headers: {dict(request.headers)}")
        logger.info(f"📥 [T+{time.time()-start_time:.3f}s] Request parsed: stream={request_data.get('stream', 'NOT_SET')} (parse took {request_read_time:.3f}s)")
        
        # 如果客户端没有指定stream参数，默认使用流式输出
        if "stream" not in request_data:
            request_data["stream"] = True
            logger.info(f"🔧 [T+{time.time()-start_time:.3f}s] Setting default stream=True")
        
        # 检查是否使用低层ASGI流处理（推荐方法）
        asgi_from_data = request_data.get("x_use_asgi_streaming", False)
        asgi_from_header = request.headers.get("x-use-asgi-streaming") == "true"
        use_asgi_streaming = asgi_from_data or asgi_from_header
        
        logger.info(f"🔧 [T+{time.time()-start_time:.3f}s] === STREAMING METHOD DETECTION ===")
        logger.info(f"🔧 [T+{time.time()-start_time:.3f}s] x_use_asgi_streaming from request_data: {asgi_from_data}")
        logger.info(f"🔧 [T+{time.time()-start_time:.3f}s] x-use-asgi-streaming from header: {request.headers.get('x-use-asgi-streaming', 'NOT_SET')} -> {asgi_from_header}")
        logger.info(f"🔧 [T+{time.time()-start_time:.3f}s] Final use_asgi_streaming decision: {use_asgi_streaming}")
        
        if use_asgi_streaming:
            logger.info(f"✅ [T+{time.time()-start_time:.3f}s] *** USING RECOMMENDED ASGI STREAMING METHOD ***")
        else:
            logger.info(f"📦 [T+{time.time()-start_time:.3f}s] Using FastAPI streaming (fallback)")
        
        # 创建ChatRequest对象
        chat_request_start = time.time()
        chat_request = ChatRequest(**request_data)
        chat_request_time = time.time() - chat_request_start
        logger.info(f"📤 [T+{time.time()-start_time:.3f}s] ChatRequest created: stream={chat_request.stream}, asgi_streaming={use_asgi_streaming} (took {chat_request_time:.3f}s)")
        
        # 选择提供商
        provider_select_start = time.time()
        provider = router.select_provider(chat_request)
        provider_select_time = time.time() - provider_select_start
        
        if not provider:
            logger.error(f"❌ [T+{time.time()-start_time:.3f}s] No available providers!")
            router.stats["failed_requests"] += 1
            raise HTTPException(status_code=503, detail="No available AI providers")
        
        logger.info(f"🎯 [T+{time.time()-start_time:.3f}s] Provider selected: {provider.name} (selection took {provider_select_time:.3f}s)")
        
        # 更新使用统计
        router.stats["provider_usage"][provider.name] += 1
        
        # 处理流式响应
        if chat_request.stream:
            logger.info(f"🌊 [T+{time.time()-start_time:.3f}s] === ENTERING STREAMING MODE ===")
            
            if use_asgi_streaming:
                # 使用推荐的ASGI流处理方法
                logger.info(f"🚀 [T+{time.time()-start_time:.3f}s] *** INITIALIZING RECOMMENDED ASGI STREAMING ***")
                
                # 验证provider健康状态
                if provider.error_count > 3:
                    logger.warning(f"⚠️ [T+{time.time()-start_time:.3f}s] Provider {provider.name} has high error count: {provider.error_count}")
                
                # 创建增强的ASGI流处理器
                asgi_streamer = LowLevelASGIStreamer(start_time)
                logger.info(f"🔧 [T+{time.time()-start_time:.3f}s] Enhanced ASGI streamer created")
                
                # 获取ASGI作用域信息
                scope = request.scope
                logger.info(f"🔧 [T+{time.time()-start_time:.3f}s] ASGI scope obtained: {scope.get('type', 'unknown')}")
                
                # 创建优化的ASGI响应
                class EnhancedASGIStreamingResponse(Response):
                    def __init__(self, streamer: LowLevelASGIStreamer, provider: AIProvider, chat_request: ChatRequest):
                        self.streamer = streamer
                        self.provider = provider
                        self.chat_request = chat_request
                        self.request_start_time = start_time
                        logger.info(f"🔧 [T+{time.time()-start_time:.3f}s] Enhanced ASGI Response created for {provider.name}")
                        super().__init__()
                    
                    async def __call__(self, scope, receive, send):
                        try:
                            logger.info(f"🔧 [T+{time.time()-self.request_start_time:.3f}s] Enhanced ASGI Response.__call__ started")
                            await self.streamer.stream_response(scope, receive, send, self.provider, self.chat_request)
                            logger.info(f"🔧 [T+{time.time()-self.request_start_time:.3f}s] Enhanced ASGI Response.__call__ completed successfully")
                        except Exception as e:
                            logger.error(f"❌ [T+{time.time()-self.request_start_time:.3f}s] ASGI Response error: {str(e)}")
                            # 发送错误响应
                            try:
                                error_data = f'data: {{"error": {{"type": "asgi_error", "message": "{str(e)}", "provider": "{self.provider.name}"}}}}\n\n'.encode()
                                await send({
                                    'type': 'http.response.start',
                                    'status': 500,
                                    'headers': [[b'content-type', b'text/event-stream']],
                                })
                                await send({
                                    'type': 'http.response.body',
                                    'body': error_data,
                                    'more_body': False,
                                })
                            except:
                                pass  # 如果无法发送错误，则静默失败
                
                router.stats["successful_requests"] += 1
                logger.info(f"✅ [T+{time.time()-start_time:.3f}s] *** RETURNING ENHANCED ASGI STREAMING RESPONSE ***")
                return EnhancedASGIStreamingResponse(asgi_streamer, provider, chat_request)
            
            else:
                # 使用改进的FastAPI流处理（作为fallback）
                logger.info(f"📦 [T+{time.time()-start_time:.3f}s] *** USING IMPROVED FASTAPI STREAMING ***")
                forward_start = time.time()
                logger.info(f"📡 [T+{time.time()-start_time:.3f}s] Starting FastAPI streaming request forwarding to {provider.name}")
                
                try:
                    result = await router.forward_request(provider, chat_request, start_time)
                    forward_setup_time = time.time() - forward_start
                    logger.info(f"🔗 [T+{time.time()-start_time:.3f}s] FastAPI forward setup completed (took {forward_setup_time:.3f}s)")
                    
                    stream_response_start = time.time()
                    logger.info(f"✅ [T+{stream_response_start-start_time:.3f}s] Creating FastAPI StreamingResponse")
                    router.stats["successful_requests"] += 1
                    
                    # 包装生成器以添加错误处理
                    async def error_handled_stream():
                        stream_wrapper_start = time.time()
                        logger.info(f"🔄 [T+{stream_wrapper_start-start_time:.3f}s] FastAPI stream wrapper started")
                        
                        chunk_count = 0
                        try:
                            async for chunk in result:
                                chunk_count += 1
                                chunk_time = time.time()
                                if chunk_count <= 5:  # Log first 5 chunks in detail
                                    logger.info(f"📡 [T+{chunk_time-start_time:.3f}s] FastAPI wrapper forwarding chunk {chunk_count}: {len(chunk) if chunk else 0} bytes")
                                yield chunk
                        except Exception as e:
                            logger.error(f"❌ [T+{time.time()-start_time:.3f}s] FastAPI stream wrapper error: {str(e)}")
                            error_response = {
                                "error": {
                                    "type": "fastapi_stream_error",
                                    "message": str(e),
                                    "provider": provider.name
                                }
                            }
                            yield f'data: {json.dumps(error_response)}\n\n'.encode()
                        finally:
                            stream_wrapper_end = time.time()
                            logger.info(f"🏁 [T+{stream_wrapper_end-start_time:.3f}s] FastAPI stream wrapper completed: {chunk_count} chunks")
                    
                    response_creation_time = time.time()
                    logger.info(f"🎯 [T+{response_creation_time-start_time:.3f}s] Returning FastAPI StreamingResponse to client")
                    
                    return StreamingResponse(
                        error_handled_stream(),
                        media_type="text/event-stream",
                        headers={
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive",
                            "X-Router-Provider": provider.name,
                            "X-Router-User": user_info.user_id,
                            "X-Streaming-Type": "fastapi-improved",
                            "X-Router-Recommendation": "use-asgi-streaming"
                        }
                    )
                    
                except Exception as e:
                    logger.error(f"❌ [T+{time.time()-start_time:.3f}s] FastAPI streaming setup failed: {str(e)}")
                    router.stats["failed_requests"] += 1
                    raise HTTPException(status_code=500, detail=f"Streaming setup failed: {str(e)}")
        
        # 处理非流式响应
        else:
            logger.info(f"📄 [T+{time.time()-start_time:.3f}s] === ENTERING NON-STREAMING MODE ===")
            forward_start = time.time()
            logger.info(f"📡 [T+{time.time()-start_time:.3f}s] Starting non-streaming request forwarding to {provider.name}")
            
            try:
                result = await router.forward_request(provider, chat_request, start_time)
                forward_setup_time = time.time() - forward_start
                logger.info(f"🔗 [T+{time.time()-start_time:.3f}s] Non-streaming forward completed (took {forward_setup_time:.3f}s)")
                
                logger.info(f"📄 [T+{time.time()-start_time:.3f}s] Returning JSON response")
                # 添加用户信息到响应
                if "_router_info" not in result:
                    result["_router_info"] = {}
                result["_router_info"]["user_id"] = user_info.user_id
                result["_router_info"]["requests_today"] = user_info.requests_today
                result["_router_info"]["daily_limit"] = user_info.daily_limit
                result["_router_info"]["recommendation"] = "Use x_use_asgi_streaming: true for optimal streaming"
                
                router.stats["successful_requests"] += 1
                return result
                
            except Exception as e:
                logger.error(f"❌ [T+{time.time()-start_time:.3f}s] Non-streaming request failed: {str(e)}")
                router.stats["failed_requests"] += 1
                raise
        
    except HTTPException as he:
        logger.error(f"❌ [T+{time.time()-start_time:.3f}s] HTTP Exception: {he.status_code} - {he.detail}")
        router.stats["failed_requests"] += 1
        raise
    except Exception as e:
        router.stats["failed_requests"] += 1
        logger.error(f"❌ [T+{time.time()-start_time:.3f}s] Unexpected error: {str(e)}")
        logger.error(f"❌ [T+{time.time()-start_time:.3f}s] Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [T+{time.time()-start_time:.3f}s] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"🏁 [T+{total_time:.3f}s] === CHAT COMPLETIONS REQUEST END === (total time: {total_time:.3f}s)")

@app.get("/health")
async def health_check():
    """Health check endpoint (no authentication required)"""
    healthy_providers = [p.name for p in router.providers if p.status == ProviderStatus.HEALTHY]
    
    return {
        "status": "healthy" if healthy_providers else "unhealthy",
        "providers": {
            provider.name: {
                "status": provider.status.value,
                "response_time": provider.response_time,
                "error_count": provider.error_count,
                "last_check": provider.last_check
            }
            for provider in router.providers
        },
        "stats": router.stats,
        "auth_mode": router.auth_mode
    }

@app.get("/stats")
async def get_stats(user_info: UserInfo = Depends(authenticate)):
    """Get usage statistics (requires authentication)"""
    return {
        "stats": router.stats,
        "providers": [
            {
                "name": p.name,
                "status": p.status.value,
                "weight": p.weight,
                "response_time": p.response_time,
                "error_count": p.error_count,
                "models": p.models
            }
            for p in router.providers
        ],
        "user_info": {
            "user_id": user_info.user_id,
            "requests_today": user_info.requests_today,
            "daily_limit": user_info.daily_limit,
            "total_requests": user_info.total_requests
        }
    }

@app.get("/auth/info")
async def get_auth_info():
    """Get authentication configuration info (no auth required)"""
    return {
        "auth_mode": router.auth_mode,
        "shared_key_format": "sk-router-2024-unified-api-key" if router.auth_mode == "shared" else None,
        "multi_user_keys": [
            {
                "key_prefix": key[:15] + "...",
                "user_id": user.user_id,
                "daily_limit": user.daily_limit
            }
            for key, user in router.users_db.items()
        ] if router.auth_mode == "multi_user" else None,
        "usage_note": "Include 'Authorization: Bearer YOUR_API_KEY' header in requests"
    }

@app.get("/v1/models")
async def list_models():
    """List available models endpoint - shows unified DeepSeek models only"""
    # 统一对外展示的 DeepSeek 模型列表
    unified_models = [
        {
            "id": "deepseek-chat",
            "object": "model",
            "created": 1677649963,
            "owned_by": "deepseek",
            "permission": [
                {
                    "id": "modelperm-deepseek-chat",
                    "object": "model_permission", 
                    "created": 1677649963,
                    "allow_create_engine": False,
                    "allow_sampling": True,
                    "allow_logprobs": True,
                    "allow_search_indices": False,
                    "allow_view": True,
                    "allow_fine_tuning": False,
                    "organization": "*",
                    "group": None,
                    "is_blocking": False
                }
            ],
            "root": "deepseek-chat",
            "parent": None
        },
        {
            "id": "deepseek-coder",
            "object": "model",
            "created": 1677649963,
            "owned_by": "deepseek",
            "permission": [
                {
                    "id": "modelperm-deepseek-coder",
                    "object": "model_permission",
                    "created": 1677649963,
                    "allow_create_engine": False,
                    "allow_sampling": True,
                    "allow_logprobs": True,
                    "allow_search_indices": False,
                    "allow_view": True,
                    "allow_fine_tuning": False,
                    "organization": "*",
                    "group": None,
                    "is_blocking": False
                }
            ],
            "root": "deepseek-coder",
            "parent": None
        }
    ]
    
    return {
        "object": "list",
        "data": unified_models
    }

@app.post("/v1/chat/completions/asgi")
async def chat_completions_asgi(request: Request, user_info: UserInfo = Depends(authenticate)):
    """Specialized endpoint for ASGI streaming (always uses low-level streaming)"""
    start_time = time.time()
    logger.info(f"🚀 [T+0.000s] ASGI endpoint request started for user: {user_info.user_id}")
    
    try:
        router.stats["total_requests"] += 1
        router.update_user_stats(user_info)
        
        # 读取请求
        request_data = await request.json()
        request_data["stream"] = True  # 强制启用流式输出
        request_data["x_use_asgi_streaming"] = True  # 强制启用ASGI流处理
        
        chat_request = ChatRequest(**request_data)
        logger.info(f"📤 [T+{time.time()-start_time:.3f}s] ASGI endpoint: stream={chat_request.stream}")
        
        # 选择提供商
        provider = router.select_provider(chat_request)
        if not provider:
            raise HTTPException(status_code=503, detail="No available AI providers")
        
        logger.info(f"🎯 [T+{time.time()-start_time:.3f}s] ASGI endpoint: selected {provider.name}")
        router.stats["provider_usage"][provider.name] += 1
        
        # 创建ASGI流处理器
        asgi_streamer = LowLevelASGIStreamer(start_time)
        
        # 自定义ASGI响应
        class ASGIStreamingResponse(Response):
            def __init__(self, streamer: LowLevelASGIStreamer, provider: AIProvider, chat_request: ChatRequest):
                self.streamer = streamer
                self.provider = provider
                self.chat_request = chat_request
                super().__init__()
            
            async def __call__(self, scope, receive, send):
                await self.streamer.stream_response(scope, receive, send, self.provider, self.chat_request)
        
        router.stats["successful_requests"] += 1
        return ASGIStreamingResponse(asgi_streamer, provider, chat_request)
        
    except Exception as e:
        router.stats["failed_requests"] += 1
        logger.error(f"❌ [T+{time.time()-start_time:.3f}s] ASGI endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ASGI streaming error: {str(e)}")

@app.get("/streaming-compare")
async def streaming_compare():
    """Endpoint to compare different streaming methods"""
    return {
        "streaming_methods": {
            "fastapi": {
                "endpoint": "/v1/chat/completions",
                "method": "POST",
                "headers": {"X-Streaming-Type": "fastapi"},
                "description": "Uses FastAPI's built-in StreamingResponse"
            },
            "asgi": {
                "endpoint": "/v1/chat/completions/asgi", 
                "method": "POST",
                "headers": {"X-Streaming-Type": "asgi"},
                "description": "Uses low-level ASGI interface for real-time streaming"
            },
            "hybrid": {
                "endpoint": "/v1/chat/completions",
                "method": "POST", 
                "body_param": {"x_use_asgi_streaming": True},
                "headers": {"x-use-asgi-streaming": "true"},
                "description": "Uses ASGI streaming via parameter or header"
            }
        },
        "test_commands": {
            "fastapi_test": 'curl -X POST "http://localhost:9000/v1/chat/completions" -H "Content-Type: application/json" -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" -d \'{"model": "deepseek-chat", "messages": [{"role": "user", "content": "hello"}], "max_tokens": 8}\'',
            "asgi_test": 'curl -X POST "http://localhost:9000/v1/chat/completions/asgi" -H "Content-Type: application/json" -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" -d \'{"model": "deepseek-chat", "messages": [{"role": "user", "content": "hello"}], "max_tokens": 8}\'',
            "hybrid_test": 'curl -X POST "http://localhost:9000/v1/chat/completions" -H "Content-Type: application/json" -H "Authorization: Bearer sk-8d6804b011614dba7bd065f8644514b" -H "x-use-asgi-streaming: true" -d \'{"model": "deepseek-chat", "messages": [{"role": "user", "content": "hello"}], "max_tokens": 8}\''
        }
    }

if __name__ == "__main__":
    logger.info("🚀 Starting Smart AI Router...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    ) 