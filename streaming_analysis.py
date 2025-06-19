#!/usr/bin/env python3

# ==============================================================================
# Streaming Analysis Script - Test and Compare Different Streaming Methods
# ==============================================================================
# Description: Comprehensive testing of AI Router streaming performance
# Author: Assistant
# Created: 2024-12-19
# Version: 1.0 - Detailed timing analysis for streaming methods
# ==============================================================================

import asyncio
import time
import json
import httpx
from typing import List, Dict, Any
import statistics

class StreamingAnalyzer:
    """Analyze streaming performance across different endpoints"""
    
    def __init__(self):
        self.base_url = "http://localhost:9000"
        self.api_key = "sk-8d6804b011614dba7bd065f8644514b"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
    async def test_endpoint(self, endpoint: str, method: str = "fastapi", headers: Dict = None) -> Dict[str, Any]:
        """Test a single endpoint and analyze timing"""
        
        test_data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "简单回答：count 1 to 5"}],
            "max_tokens": 20,
            "stream": True
        }
        
        if method == "asgi_param":
            test_data["x_use_asgi_streaming"] = True
        
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)
        
        start_time = time.time()
        chunk_times = []
        chunk_sizes = []
        chunk_intervals = []
        total_content = ""
        
        print(f"\n{'='*60}")
        print(f"🧪 Testing {method.upper()} method on {endpoint}")
        print(f"{'='*60}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                first_chunk_time = None
                last_chunk_time = start_time
                chunk_count = 0
                
                async with client.stream(
                    "POST",
                    f"{self.base_url}{endpoint}",
                    headers=request_headers,
                    json=test_data
                ) as response:
                    
                    if response.status_code != 200:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status_code}",
                            "method": method
                        }
                    
                    print(f"📡 Response started (status: {response.status_code})")
                    print(f"📋 Response headers: {dict(response.headers)}")
                    
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            current_time = time.time()
                            chunk_count += 1
                            
                            if first_chunk_time is None:
                                first_chunk_time = current_time
                                time_to_first_byte = (first_chunk_time - start_time) * 1000
                                print(f"⚡ Time to first byte: {time_to_first_byte:.1f}ms")
                            
                            interval = (current_time - last_chunk_time) * 1000  # ms
                            chunk_times.append((current_time - start_time) * 1000)
                            chunk_sizes.append(len(chunk))
                            if chunk_count > 1:  # Skip first interval
                                chunk_intervals.append(interval)
                            
                            # Log first few chunks
                            if chunk_count <= 10:
                                chunk_text = chunk.decode('utf-8', errors='ignore')[:50].replace('\n', '\\n')
                                print(f"📦 Chunk {chunk_count:3d}: {len(chunk):4d}B (+{interval:5.1f}ms) - {chunk_text}")
                            
                            total_content += chunk.decode('utf-8', errors='ignore')
                            last_chunk_time = current_time
                
                total_time = (time.time() - start_time) * 1000
                
                # Analysis
                result = {
                    "success": True,
                    "method": method,
                    "endpoint": endpoint,
                    "total_time_ms": total_time,
                    "time_to_first_byte_ms": (first_chunk_time - start_time) * 1000 if first_chunk_time else None,
                    "total_chunks": chunk_count,
                    "total_bytes": sum(chunk_sizes),
                    "chunk_intervals_ms": chunk_intervals,
                    "avg_interval_ms": statistics.mean(chunk_intervals) if chunk_intervals else 0,
                    "min_interval_ms": min(chunk_intervals) if chunk_intervals else 0,
                    "max_interval_ms": max(chunk_intervals) if chunk_intervals else 0,
                    "zero_intervals": sum(1 for x in chunk_intervals if x < 1.0) if chunk_intervals else 0,
                    "zero_interval_percentage": (sum(1 for x in chunk_intervals if x < 1.0) / len(chunk_intervals) * 100) if chunk_intervals else 0,
                    "content_preview": total_content[:200]
                }
                
                print(f"\n📊 Analysis Results:")
                print(f"   ⏱️  Total time: {total_time:.1f}ms")
                print(f"   🚀 Time to first byte: {result['time_to_first_byte_ms']:.1f}ms")
                print(f"   📦 Total chunks: {chunk_count}")
                print(f"   📏 Total bytes: {sum(chunk_sizes)}")
                if chunk_intervals:
                    print(f"   📈 Avg chunk interval: {result['avg_interval_ms']:.1f}ms")
                    print(f"   ⚡ Min interval: {result['min_interval_ms']:.1f}ms")
                    print(f"   🐌 Max interval: {result['max_interval_ms']:.1f}ms")
                    print(f"   🟢 Zero intervals: {result['zero_intervals']}/{len(chunk_intervals)} ({result['zero_interval_percentage']:.1f}%)")
                
                return result
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "method": method
            }
    
    async def compare_all_methods(self):
        """Compare all streaming methods"""
        
        print(f"\n🔬 AI Router Streaming Performance Analysis")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        # Test configurations
        tests = [
            {
                "name": "FastAPI Standard",
                "endpoint": "/v1/chat/completions",
                "method": "fastapi",
                "headers": {}
            },
            {
                "name": "ASGI Dedicated Endpoint",
                "endpoint": "/v1/chat/completions/asgi",
                "method": "asgi_endpoint",
                "headers": {}
            },
            {
                "name": "ASGI via Header",
                "endpoint": "/v1/chat/completions",
                "method": "asgi_header",
                "headers": {"x-use-asgi-streaming": "true"}
            },
            {
                "name": "ASGI via Parameter",
                "endpoint": "/v1/chat/completions",
                "method": "asgi_param",
                "headers": {}
            }
        ]
        
        results = []
        
        for test in tests:
            print(f"\n⏳ Running test: {test['name']}")
            await asyncio.sleep(2)  # Brief pause between tests
            
            result = await self.test_endpoint(
                test["endpoint"],
                test["method"],
                test["headers"]
            )
            result["test_name"] = test["name"]
            results.append(result)
        
        # Summary comparison
        print(f"\n🏆 PERFORMANCE COMPARISON SUMMARY")
        print(f"{'='*80}")
        
        successful_results = [r for r in results if r["success"]]
        
        if successful_results:
            print(f"{'Method':<25} {'TTFB(ms)':<10} {'Total(ms)':<12} {'Chunks':<8} {'Avg Int(ms)':<12} {'Zero %':<8}")
            print(f"{'-'*80}")
            
            for result in successful_results:
                ttfb = f"{result['time_to_first_byte_ms']:.1f}" if result['time_to_first_byte_ms'] else "N/A"
                total = f"{result['total_time_ms']:.1f}"
                chunks = str(result['total_chunks'])
                avg_int = f"{result['avg_interval_ms']:.1f}"
                zero_pct = f"{result['zero_interval_percentage']:.1f}%"
                
                print(f"{result['test_name']:<25} {ttfb:<10} {total:<12} {chunks:<8} {avg_int:<12} {zero_pct:<8}")
            
            # Find best performers
            print(f"\n🥇 Best Performers:")
            
            # Fastest first byte
            fastest_ttfb = min(successful_results, key=lambda x: x['time_to_first_byte_ms'] or float('inf'))
            print(f"   ⚡ Fastest first byte: {fastest_ttfb['test_name']} ({fastest_ttfb['time_to_first_byte_ms']:.1f}ms)")
            
            # Lowest zero interval percentage (most real-time)
            most_realtime = min(successful_results, key=lambda x: x['zero_interval_percentage'])
            print(f"   🎯 Most real-time: {most_realtime['test_name']} ({most_realtime['zero_interval_percentage']:.1f}% zero intervals)")
            
            # Overall fastest
            fastest_total = min(successful_results, key=lambda x: x['total_time_ms'])
            print(f"   🏃 Fastest total: {fastest_total['test_name']} ({fastest_total['total_time_ms']:.1f}ms)")
        
        # Failed tests
        failed_results = [r for r in results if not r["success"]]
        if failed_results:
            print(f"\n❌ Failed Tests:")
            for result in failed_results:
                print(f"   • {result.get('test_name', 'Unknown')}: {result['error']}")
        
        return results

async def main():
    """Main analysis function"""
    analyzer = StreamingAnalyzer()
    results = await analyzer.compare_all_methods()
    
    # Save detailed results
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = f"streaming_analysis_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed results saved to: {filename}")
    print(f"\n✅ Analysis completed!")

if __name__ == "__main__":
    asyncio.run(main()) 