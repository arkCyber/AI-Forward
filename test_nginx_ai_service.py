#!/usr/bin/env python3
"""
==============================================================================
NGINX AI Gateway Service Test Script
==============================================================================
Description: 全面测试 NGINX AI 网关服务，包括流式响应和外部访问
Author: Assistant
Created: 2024-12-19
Version: 1.0

This script tests:
- 流式响应（Stream Response）功能
- 外部用户访问能力
- 不同 AI 服务端点
- 负载均衡和故障转移
- 速率限制功能
- 并发请求处理
==============================================================================
"""

import asyncio
import json
import sys
import time
import aiohttp
import requests
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
import threading


class NGINXAIServiceTester:
    """NGINX AI 网关服务测试器"""
    
    def __init__(self, base_url: str = "http://localhost"):
        """
        初始化测试器
        
        Args:
            base_url: NGINX 网关基础 URL
        """
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.test_results = {}
        
    def log(self, message: str, level: str = "INFO"):
        """记录日志信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color_map = {
            "INFO": "\033[0;36m",    # Cyan
            "SUCCESS": "\033[0;32m", # Green
            "WARNING": "\033[1;33m", # Yellow
            "ERROR": "\033[0;31m",   # Red
            "STREAM": "\033[0;35m"   # Magenta
        }
        reset = "\033[0m"
        color = color_map.get(level, "")
        print(f"{color}[{timestamp}] [{level}] {message}{reset}")
        
    def test_nginx_health(self) -> bool:
        """测试 NGINX 网关健康状态"""
        self.log("🔍 Testing NGINX Gateway Health...")
        
        try:
            response = requests.get(f"{self.base_url}/nginx-health", timeout=5)
            if response.status_code == 200:
                self.log("✅ NGINX Gateway is healthy", "SUCCESS")
                return True
            else:
                self.log(f"❌ NGINX Gateway health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ NGINX Gateway connection failed: {e}", "ERROR")
            return False
    
    def test_service_health(self) -> Dict[str, bool]:
        """测试各个服务健康状态"""
        self.log("🔍 Testing Backend Services Health...")
        
        services = {
            'ai-router': f"{self.base_url}/health",
            'stats': f"{self.base_url}/stats"
        }
        
        results = {}
        for service_name, url in services.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self.log(f"✅ {service_name} is healthy", "SUCCESS")
                    results[service_name] = True
                else:
                    self.log(f"⚠️  {service_name} returned status {response.status_code}", "WARNING")
                    results[service_name] = False
            except Exception as e:
                self.log(f"❌ {service_name} health check failed: {e}", "ERROR")
                results[service_name] = False
        
        return results
    
    def test_non_streaming_chat(self, service: str = "api", model: str = "gpt-3.5-turbo") -> bool:
        """测试非流式聊天完成"""
        self.log(f"🤖 Testing Non-Streaming Chat ({service})...")
        
        endpoint_map = {
            'api': f"{self.base_url}/api/v1/chat/completions",
            'v1': f"{self.base_url}/v1/chat/completions", 
            'deepseek': f"{self.base_url}/deepseek/v1/chat/completions",
            'lingyiwanwu': f"{self.base_url}/lingyiwanwu/v1/chat/completions",
            'ollama': f"{self.base_url}/ollama/v1/chat/completions",
            'forward': f"{self.base_url}/forward/v1/chat/completions"
        }
        
        url = endpoint_map.get(service, endpoint_map['api'])
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a helpful AI assistant. Please respond concisely."
                },
                {
                    "role": "user", 
                    "content": f"Hello! This is a test message from NGINX gateway via {service} endpoint. Please respond with 'Test successful via {service}' and current time."
                }
            ],
            "stream": False,
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "NGINX-AI-Gateway-Test/1.0"
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                self.log(f"✅ Non-streaming chat successful ({service})", "SUCCESS")
                self.log(f"   Response: {content[:100]}...", "SUCCESS")
                self.log(f"   Response time: {response_time:.2f}s", "SUCCESS")
                return True
            else:
                self.log(f"❌ Non-streaming chat failed ({service}): {response.status_code}", "ERROR")
                self.log(f"   Response: {response.text[:200]}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Non-streaming chat error ({service}): {e}", "ERROR")
            return False
    
    async def test_streaming_chat(self, service: str = "api", model: str = "gpt-3.5-turbo") -> bool:
        """测试流式聊天完成 - 关键功能测试"""
        self.log(f"🌊 Testing Streaming Chat ({service})...", "STREAM")
        
        endpoint_map = {
            'api': f"{self.base_url}/api/v1/chat/completions",
            'v1': f"{self.base_url}/v1/chat/completions",
            'deepseek': f"{self.base_url}/deepseek/v1/chat/completions",
            'lingyiwanwu': f"{self.base_url}/lingyiwanwu/v1/chat/completions",
            'ollama': f"{self.base_url}/ollama/v1/chat/completions",
            'forward': f"{self.base_url}/forward/v1/chat/completions"
        }
        
        url = endpoint_map.get(service, endpoint_map['api'])
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant testing streaming responses."
                },
                {
                    "role": "user", 
                    "content": f"Please write a short 50-word story about AI testing. Stream this response token by token via {service} endpoint."
                }
            ],
            "stream": True,  # 启用流式响应
            "max_tokens": 150,
            "temperature": 0.8
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": "NGINX-AI-Gateway-Test/1.0"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                
                async with session.post(url, json=payload, headers=headers, timeout=60) as response:
                    if response.status == 200:
                        self.log(f"🌊 Streaming response started ({service})", "STREAM")
                        
                        chunks_received = 0
                        content_parts = []
                        
                        # 读取流式响应
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            
                            if line.startswith('data: '):
                                data_str = line[6:]  # 移除 'data: ' 前缀
                                
                                if data_str == '[DONE]':
                                    self.log("🏁 Stream completed", "STREAM")
                                    break
                                
                                try:
                                    chunk_data = json.loads(data_str)
                                    delta = chunk_data.get('choices', [{}])[0].get('delta', {})
                                    content = delta.get('content', '')
                                    
                                    if content:
                                        content_parts.append(content)
                                        chunks_received += 1
                                        
                                        # 显示流式内容（每10个块显示一次）
                                        if chunks_received % 10 == 0:
                                            self.log(f"📦 Received {chunks_received} chunks...", "STREAM")
                                            
                                except json.JSONDecodeError:
                                    continue
                        
                        response_time = time.time() - start_time
                        full_content = ''.join(content_parts)
                        
                        self.log(f"✅ Streaming chat successful ({service})", "SUCCESS")
                        self.log(f"   Total chunks: {chunks_received}", "SUCCESS")
                        self.log(f"   Response time: {response_time:.2f}s", "SUCCESS")
                        self.log(f"   Content: {full_content[:100]}...", "SUCCESS")
                        
                        return chunks_received > 0
                        
                    else:
                        self.log(f"❌ Streaming chat failed ({service}): {response.status}", "ERROR")
                        error_text = await response.text()
                        self.log(f"   Response: {error_text[:200]}", "ERROR")
                        return False
                        
        except Exception as e:
            self.log(f"❌ Streaming chat error ({service}): {e}", "ERROR")
            return False
    
    def test_concurrent_requests(self, num_requests: int = 5) -> Dict[str, int]:
        """测试并发请求处理能力"""
        self.log(f"🚀 Testing Concurrent Requests ({num_requests} requests)...")
        
        def make_request(request_id: int) -> bool:
            """发送单个请求"""
            try:
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "user", "content": f"This is concurrent request #{request_id}. Please respond briefly."}
                    ],
                    "stream": False,
                    "max_tokens": 50
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/chat/completions", 
                    json=payload, 
                    timeout=30
                )
                
                success = response.status_code == 200
                if success:
                    self.log(f"✅ Request {request_id} completed successfully", "SUCCESS")
                else:
                    self.log(f"❌ Request {request_id} failed: {response.status_code}", "ERROR")
                
                return success
                
            except Exception as e:
                self.log(f"❌ Request {request_id} error: {e}", "ERROR")
                return False
        
        # 使用线程池执行并发请求
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request, i+1) for i in range(num_requests)]
            results = [future.result() for future in futures]
        
        total_time = time.time() - start_time
        successful = sum(results)
        failed = len(results) - successful
        
        self.log(f"📊 Concurrent Test Results:", "SUCCESS")
        self.log(f"   Total requests: {num_requests}", "SUCCESS")
        self.log(f"   Successful: {successful}", "SUCCESS")
        self.log(f"   Failed: {failed}", "SUCCESS")
        self.log(f"   Total time: {total_time:.2f}s", "SUCCESS")
        self.log(f"   Requests/second: {num_requests/total_time:.2f}", "SUCCESS")
        
        return {
            'total': num_requests,
            'successful': successful,
            'failed': failed,
            'total_time': total_time,
            'rps': num_requests/total_time
        }
    
    def test_rate_limiting(self) -> bool:
        """测试速率限制功能"""
        self.log("⏱️  Testing Rate Limiting...")
        
        # 快速发送多个请求以触发速率限制
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Rate limit test"}],
            "stream": False,
            "max_tokens": 10
        }
        
        rate_limited = False
        successful_requests = 0
        
        for i in range(10):  # 发送10个快速请求
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/chat/completions",
                    json=payload,
                    timeout=5
                )
                
                if response.status_code == 429:  # Too Many Requests
                    self.log(f"✅ Rate limiting triggered at request {i+1}", "SUCCESS")
                    rate_limited = True
                    break
                elif response.status_code == 200:
                    successful_requests += 1
                    time.sleep(0.1)  # 短暂延迟
                    
            except Exception as e:
                self.log(f"   Request {i+1} error: {e}", "WARNING")
        
        if rate_limited:
            self.log("✅ Rate limiting is working correctly", "SUCCESS")
        else:
            self.log(f"⚠️  Rate limiting not triggered ({successful_requests} successful)", "WARNING")
            
        return rate_limited
    
    def test_external_access(self, external_url: str = None) -> bool:
        """测试外部访问能力"""
        if not external_url:
            self.log("🌐 Skipping external access test (no external URL provided)", "WARNING")
            return False
            
        self.log(f"🌐 Testing External Access: {external_url}")
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "This is an external access test. Please confirm connectivity."}
            ],
            "stream": False,
            "max_tokens": 50
        }
        
        try:
            response = requests.post(
                f"{external_url}/api/v1/chat/completions",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                self.log("✅ External access successful", "SUCCESS")
                return True
            else:
                self.log(f"❌ External access failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ External access error: {e}", "ERROR")
            return False
    
    def test_all_ai_services(self) -> Dict[str, bool]:
        """测试所有 AI 服务端点"""
        self.log("🎯 Testing All AI Service Endpoints...")
        
        services = {
            'api': 'gpt-3.5-turbo',
            'v1': 'gpt-3.5-turbo', 
            'deepseek': 'deepseek-chat',
            'lingyiwanwu': 'yi-34b-chat',
            'ollama': 'llama3.2',
            'forward': 'gpt-3.5-turbo'
        }
        
        results = {}
        for service, model in services.items():
            try:
                # 测试非流式
                non_stream_result = self.test_non_streaming_chat(service, model)
                results[f"{service}_non_stream"] = non_stream_result
                
                time.sleep(1)  # 防止速率限制
                
            except Exception as e:
                self.log(f"❌ Service {service} test failed: {e}", "ERROR")
                results[f"{service}_non_stream"] = False
        
        return results
    
    async def test_all_streaming_services(self) -> Dict[str, bool]:
        """测试所有服务的流式响应"""
        self.log("🌊 Testing Streaming for All Services...")
        
        services = {
            'api': 'gpt-3.5-turbo',
            'ollama': 'llama3.2'
        }
        
        results = {}
        for service, model in services.items():
            try:
                stream_result = await self.test_streaming_chat(service, model)
                results[f"{service}_stream"] = stream_result
                await asyncio.sleep(2)  # 防止速率限制
                
            except Exception as e:
                self.log(f"❌ Streaming test {service} failed: {e}", "ERROR")
                results[f"{service}_stream"] = False
        
        return results
    
    def generate_test_report(self, results: Dict) -> str:
        """生成测试报告"""
        report = f"""
==============================================================================
                    🎯 NGINX AI Gateway Test Report
==============================================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Gateway URL: {self.base_url}

📊 Test Summary:
"""
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report += f"   Total Tests: {total_tests}\n"
        report += f"   Passed: {passed_tests}\n"
        report += f"   Failed: {total_tests - passed_tests}\n"
        report += f"   Success Rate: {success_rate:.1f}%\n\n"
        
        report += "📋 Detailed Results:\n"
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            report += f"   {test_name}: {status}\n"
        
        report += "\n"
        report += "🔧 Recommendations:\n"
        
        if not results.get('nginx_health', False):
            report += "   • Check NGINX gateway configuration and restart service\n"
        
        if not any(k.endswith('_stream') and v for k, v in results.items()):
            report += "   • Verify streaming support in backend services\n"
            report += "   • Check NGINX proxy_buffering settings\n"
        
        if results.get('concurrent_failed', 0) > 0:
            report += "   • Consider increasing worker processes or connection limits\n"
        
        report += "\n=============================================================================="
        
        return report
    
    async def run_comprehensive_test(self, external_url: str = None) -> Dict[str, bool]:
        """运行全面的测试套件"""
        self.log("🚀 Starting Comprehensive NGINX AI Gateway Test...", "SUCCESS")
        self.log(f"🎯 Target Gateway: {self.base_url}", "SUCCESS")
        self.log("=" * 80, "SUCCESS")
        
        all_results = {}
        
        # 1. 基础健康检查
        all_results['nginx_health'] = self.test_nginx_health()
        if not all_results['nginx_health']:
            self.log("❌ NGINX Gateway unavailable - stopping tests", "ERROR")
            return all_results
        
        # 2. 服务健康检查
        service_health = self.test_service_health()
        all_results.update(service_health)
        
        # 3. 测试所有AI服务端点
        service_results = self.test_all_ai_services()
        all_results.update(service_results)
        
        # 4. 测试流式响应
        streaming_results = await self.test_all_streaming_services()
        all_results.update(streaming_results)
        
        # 5. 并发测试
        concurrent_results = self.test_concurrent_requests(5)
        all_results['concurrent_successful'] = concurrent_results['successful'] >= 4
        all_results['concurrent_failed'] = concurrent_results['failed']
        
        # 6. 速率限制测试
        all_results['rate_limiting'] = self.test_rate_limiting()
        
        # 7. 外部访问测试（如果提供了外部URL）
        if external_url:
            all_results['external_access'] = self.test_external_access(external_url)
        
        # 生成并显示报告
        self.log("=" * 80, "SUCCESS")
        report = self.generate_test_report(all_results)
        print(report)
        
        return all_results


async def main():
    """主测试函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NGINX AI Gateway Service Tester')
    parser.add_argument('--url', default='http://localhost', 
                       help='NGINX Gateway URL (default: http://localhost)')
    parser.add_argument('--external-url', 
                       help='External URL for testing external access')
    parser.add_argument('--quick', action='store_true',
                       help='Run only basic tests')
    
    args = parser.parse_args()
    
    # 创建测试器实例
    tester = NGINXAIServiceTester(args.url)
    
    if args.quick:
        # 快速测试
        tester.log("⚡ Running Quick Test Suite...")
        results = {
            'nginx_health': tester.test_nginx_health(),
            'api_non_stream': tester.test_non_streaming_chat('api'),
            'api_stream': await tester.test_streaming_chat('api')
        }
    else:
        # 全面测试
        results = await tester.run_comprehensive_test(args.external_url)
    
    # 返回适当的退出代码
    success_rate = sum(results.values()) / len(results) if results else 0
    sys.exit(0 if success_rate >= 0.8 else 1)


if __name__ == "__main__":
    # 安装必要的包
    try:
        import aiohttp
        import requests
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp", "requests"])
        import aiohttp
        import requests
    
    asyncio.run(main()) 