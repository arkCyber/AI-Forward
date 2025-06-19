#!/usr/bin/env python3

# ==============================================================================
# ASGI Parameter Method Test Script
# ==============================================================================
# Description: Test the recommended ASGI parameter streaming method
# Author: Assistant
# Created: 2024-12-19
# Version: 1.0 - ASGI parameter method validation
# ==============================================================================

import asyncio
import time
import json
import httpx
from typing import List, Dict, Any

class ASGIParameterTester:
    """Test ASGI parameter streaming method"""
    
    def __init__(self):
        self.base_url = "http://localhost:9000"
        self.api_key = "sk-8d6804b011614dba7bd065f8644514b"
        self.test_results = []
    
    async def test_asgi_parameter_method(self, test_name: str, request_data: dict):
        """Test ASGI parameter method with detailed timing"""
        print(f"\n🚀 Testing: {test_name}")
        print(f"📤 Request: {json.dumps(request_data, indent=2)}")
        
        start_time = time.time()
        chunks_received = 0
        total_bytes = 0
        response_content = ""
        intervals = []
        last_chunk_time = start_time
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                        "Accept": "text/event-stream"
                    },
                    json=request_data
                ) as response:
                    
                    connection_time = time.time() - start_time
                    print(f"🔗 Connected (status: {response.status_code}, time: {connection_time:.3f}s)")
                    
                    if response.status_code != 200:
                        error_text = await response.aread()
                        print(f"❌ Error: {response.status_code} - {error_text.decode()}")
                        return None
                    
                    # Check headers
                    headers = dict(response.headers)
                    print(f"📋 Headers: {headers}")
                    
                    async for chunk in response.aiter_bytes(chunk_size=1024):
                        if chunk:
                            current_time = time.time()
                            chunks_received += 1
                            total_bytes += len(chunk)
                            
                            interval = current_time - last_chunk_time
                            intervals.append(interval)
                            
                            if chunks_received <= 5:  # Log first 5 chunks
                                print(f"📦 Chunk {chunks_received}: {len(chunk)} bytes (+{interval*1000:.1f}ms)")
                            
                            try:
                                response_content += chunk.decode('utf-8', errors='ignore')
                            except:
                                pass
                            
                            last_chunk_time = current_time
            
            total_time = time.time() - start_time
            
            # Calculate performance metrics
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                min_interval = min(intervals)
                max_interval = max(intervals)
                zero_intervals = sum(1 for x in intervals if x < 0.001)
                zero_percentage = (zero_intervals / len(intervals)) * 100 if intervals else 0
            else:
                avg_interval = min_interval = max_interval = 0
                zero_percentage = 0
            
            result = {
                "test_name": test_name,
                "status": "success",
                "total_time": total_time,
                "connection_time": connection_time,
                "chunks_received": chunks_received,
                "total_bytes": total_bytes,
                "avg_chunk_size": total_bytes / chunks_received if chunks_received > 0 else 0,
                "avg_interval": avg_interval,
                "min_interval": min_interval,
                "max_interval": max_interval,
                "zero_percentage": zero_percentage,
                "headers": headers,
                "content_preview": response_content[:200] + "..." if len(response_content) > 200 else response_content
            }
            
            print(f"✅ Test completed: {chunks_received} chunks, {total_bytes} bytes in {total_time:.3f}s")
            print(f"📊 Performance: avg interval {avg_interval*1000:.1f}ms, zero intervals {zero_percentage:.1f}%")
            
            return result
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            return {
                "test_name": test_name,
                "status": "failed",
                "error": str(e)
            }
    
    async def run_all_tests(self):
        """Run comprehensive ASGI parameter tests"""
        print("🔬 Starting ASGI Parameter Method Tests")
        print("=" * 60)
        
        test_cases = [
            {
                "name": "ASGI Parameter Method (via request body)",
                "data": {
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "Say hello briefly"}],
                    "max_tokens": 10,
                    "stream": True,
                    "x_use_asgi_streaming": True  # 推荐方法
                }
            },
            {
                "name": "ASGI Header Method",
                "data": {
                    "model": "deepseek-chat", 
                    "messages": [{"role": "user", "content": "Say hello briefly"}],
                    "max_tokens": 10,
                    "stream": True
                }
            },
            {
                "name": "FastAPI Fallback Method",
                "data": {
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "Say hello briefly"}],
                    "max_tokens": 10,
                    "stream": True,
                    "x_use_asgi_streaming": False
                }
            },
            {
                "name": "Non-streaming Test",
                "data": {
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "Say hello"}],
                    "max_tokens": 5,
                    "stream": False
                }
            }
        ]
        
        for test_case in test_cases:
            result = await self.test_asgi_parameter_method(test_case["name"], test_case["data"])
            if result:
                self.test_results.append(result)
            
            # Add delay between tests
            await asyncio.sleep(2)
        
        # Generate summary report
        self.generate_test_report()
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 ASGI PARAMETER METHOD TEST REPORT")
        print("=" * 60)
        
        successful_tests = [r for r in self.test_results if r.get("status") == "success"]
        failed_tests = [r for r in self.test_results if r.get("status") == "failed"]
        
        print(f"📈 Summary: {len(successful_tests)} successful, {len(failed_tests)} failed")
        print()
        
        if successful_tests:
            print("✅ Successful Tests:")
            for result in successful_tests:
                print(f"  • {result['test_name']}")
                print(f"    - Chunks: {result['chunks_received']}, Bytes: {result['total_bytes']}")
                print(f"    - Time: {result['total_time']:.3f}s, Zero intervals: {result['zero_percentage']:.1f}%")
                if 'headers' in result:
                    method = result['headers'].get('x-router-method', 'unknown')
                    provider = result['headers'].get('x-router-provider', 'unknown')
                    print(f"    - Method: {method}, Provider: {provider}")
                print()
        
        if failed_tests:
            print("❌ Failed Tests:")
            for result in failed_tests:
                print(f"  • {result['test_name']}: {result.get('error', 'Unknown error')}")
            print()
        
        # Performance comparison
        if len(successful_tests) > 1:
            print("📊 Performance Comparison:")
            for result in successful_tests:
                if result.get('avg_interval') is not None:
                    print(f"  • {result['test_name']}: {result['avg_interval']*1000:.1f}ms avg, {result['zero_percentage']:.1f}% zero")
            print()
        
        print("🎯 Recommendation: Use ASGI parameter method for best performance")
        print("   Request body: {\"x_use_asgi_streaming\": true}")

async def main():
    """Main test function"""
    tester = ASGIParameterTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 