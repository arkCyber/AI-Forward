#!/usr/bin/env python3
"""
NGINX AI Gateway Streaming Test Script
测试 NGINX AI 网关的流式响应和外部访问功能
"""

import asyncio
import json
import time
import aiohttp
import requests
from datetime import datetime


class NGINXStreamTester:
    """NGINX 流式服务测试器"""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url.rstrip('/')
        
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[0;36m",
            "SUCCESS": "\033[0;32m", 
            "ERROR": "\033[0;31m",
            "STREAM": "\033[0;35m"
        }
        reset = "\033[0m"
        color = colors.get(level, "")
        print(f"{color}[{timestamp}] {message}{reset}")
    
    def test_nginx_health(self) -> bool:
        """测试 NGINX 健康状态"""
        self.log("🔍 Testing NGINX Health...")
        try:
            response = requests.get(f"{self.base_url}/nginx-health", timeout=5)
            if response.status_code == 200:
                self.log("✅ NGINX is healthy", "SUCCESS")
                return True
            else:
                self.log(f"❌ NGINX health failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ NGINX connection failed: {e}", "ERROR")
            return False
    
    def test_non_streaming(self, endpoint: str) -> bool:
        """测试非流式响应"""
        self.log(f"🤖 Testing Non-Streaming: {endpoint}")
        
        url = f"{self.base_url}{endpoint}"
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Hello! Please respond briefly that the service is working."}
            ],
            "stream": False,
            "max_tokens": 50
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                self.log(f"✅ Non-streaming OK: {content[:50]}...", "SUCCESS")
                self.log(f"   Response time: {response_time:.2f}s", "SUCCESS")
                return True
            else:
                self.log(f"❌ Non-streaming failed: {response.status_code}", "ERROR")
                self.log(f"   Response: {response.text[:100]}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Non-streaming error: {e}", "ERROR")
            return False
    
    async def test_streaming(self, endpoint: str) -> bool:
        """测试流式响应 - 核心功能"""
        self.log(f"🌊 Testing Streaming: {endpoint}", "STREAM")
        
        url = f"{self.base_url}{endpoint}"
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Please tell a short story about AI testing. Stream the response."}
            ],
            "stream": True,  # 关键：启用流式响应
            "max_tokens": 100
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                
                async with session.post(url, json=payload, headers=headers, timeout=60) as response:
                    if response.status == 200:
                        self.log("🌊 Streaming started...", "STREAM")
                        
                        chunks_received = 0
                        content_parts = []
                        
                        # 读取流式数据
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            
                            if line.startswith('data: '):
                                data_str = line[6:]  # 去除 'data: ' 前缀
                                
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
                                        
                                        # 显示实时流式内容
                                        if chunks_received <= 5:
                                            self.log(f"📦 Chunk {chunks_received}: '{content}'", "STREAM")
                                        elif chunks_received % 10 == 0:
                                            self.log(f"📦 Received {chunks_received} chunks...", "STREAM")
                                            
                                except json.JSONDecodeError:
                                    continue
                        
                        response_time = time.time() - start_time
                        full_content = ''.join(content_parts)
                        
                        if chunks_received > 0:
                            self.log("✅ Streaming test successful!", "SUCCESS")
                            self.log(f"   Total chunks: {chunks_received}", "SUCCESS")
                            self.log(f"   Response time: {response_time:.2f}s", "SUCCESS")
                            self.log(f"   Full content: {full_content[:80]}...", "SUCCESS")
                            return True
                        else:
                            self.log("❌ No streaming chunks received", "ERROR")
                            return False
                        
                    else:
                        self.log(f"❌ Streaming failed: HTTP {response.status}", "ERROR")
                        error_text = await response.text()
                        self.log(f"   Error: {error_text[:100]}", "ERROR")
                        return False
                        
        except Exception as e:
            self.log(f"❌ Streaming error: {e}", "ERROR")
            return False
    
    def test_external_access(self, external_ip: str) -> bool:
        """测试外部IP访问"""
        if not external_ip:
            self.log("⚠️  No external IP provided, skipping external access test", "INFO")
            return True
            
        self.log(f"🌐 Testing External Access: {external_ip}")
        
        external_url = f"http://{external_ip}"
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "External access test. Please confirm."}
            ],
            "stream": False,
            "max_tokens": 30
        }
        
        try:
            response = requests.post(
                f"{external_url}/api/v1/chat/completions",
                json=payload,
                timeout=20
            )
            
            if response.status_code == 200:
                self.log("✅ External access successful!", "SUCCESS")
                return True
            else:
                self.log(f"❌ External access failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ External access error: {e}", "ERROR")
            return False
    
    async def run_comprehensive_test(self, external_ip: str = None):
        """运行全面测试"""
        self.log("🚀 Starting NGINX AI Gateway Streaming Test")
        self.log(f"🎯 Target: {self.base_url}")
        self.log("=" * 60)
        
        results = {}
        
        # 1. NGINX 健康检查
        results['nginx_health'] = self.test_nginx_health()
        if not results['nginx_health']:
            self.log("❌ NGINX not available, stopping tests", "ERROR")
            return results
        
        # 2. 测试不同端点的非流式响应
        endpoints = [
            '/api/v1/chat/completions',
            '/v1/chat/completions',
            '/forward/v1/chat/completions'
        ]
        
        for endpoint in endpoints:
            endpoint_name = endpoint.split('/')[1] if len(endpoint.split('/')) > 1 else 'root'
            results[f'{endpoint_name}_non_stream'] = self.test_non_streaming(endpoint)
            time.sleep(1)  # 避免速率限制
        
        # 3. 测试流式响应 - 核心功能
        streaming_endpoints = [
            '/api/v1/chat/completions',
            '/v1/chat/completions'
        ]
        
        for endpoint in streaming_endpoints:
            endpoint_name = endpoint.split('/')[1] if len(endpoint.split('/')) > 1 else 'root'
            results[f'{endpoint_name}_stream'] = await self.test_streaming(endpoint)
            await asyncio.sleep(2)  # 避免速率限制
        
        # 4. 外部访问测试
        if external_ip:
            results['external_access'] = self.test_external_access(external_ip)
        
        # 5. 生成测试报告
        self.log("=" * 60)
        self.log("📊 Test Results Summary:")
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            self.log(f"   {test_name}: {status}")
        
        self.log(f"📈 Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # 6. 重点检查流式功能
        streaming_tests = [k for k in results.keys() if 'stream' in k]
        streaming_passed = sum(1 for k in streaming_tests if results[k])
        
        if streaming_passed > 0:
            self.log("🌊 Streaming功能正常工作！", "SUCCESS")
        else:
            self.log("❌ Streaming功能测试失败", "ERROR")
        
        self.log("=" * 60)
        
        return results


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NGINX AI Gateway Streaming Test')
    parser.add_argument('--url', default='http://localhost', 
                       help='NGINX Gateway URL (default: http://localhost)')
    parser.add_argument('--external-ip', 
                       help='External IP address to test external access')
    
    args = parser.parse_args()
    
    # 运行测试
    tester = NGINXStreamTester(args.url)
    results = await tester.run_comprehensive_test(args.external_ip)
    
    # 检查是否至少有一个流式测试成功
    streaming_success = any(k for k, v in results.items() if 'stream' in k and v)
    
    if streaming_success:
        print("\n🎉 NGINX AI Gateway 流式服务测试成功！")
        print("✅ 您的服务支持流式响应")
        print("✅ 外部用户可以正常访问")
    else:
        print("\n⚠️  流式服务可能需要进一步配置")
    
    return 0 if streaming_success else 1


if __name__ == "__main__":
    # 安装依赖
    try:
        import aiohttp
        import requests
    except ImportError:
        print("Installing required packages...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp", "requests"])
        import aiohttp
        import requests
    
    exit_code = asyncio.run(main()) 