#!/usr/bin/env python3
"""
==============================================================================
Remote Ollama Connection Test Script
==============================================================================
Description: Test connectivity and functionality of remote Ollama server
Author: Assistant  
Created: 2024-12-19
Version: 1.0

This script helps verify that your remote Ollama server is properly
configured and accessible before deploying the AI Gateway.
==============================================================================
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import requests


class RemoteOllamaTest:
    """Test remote Ollama server connectivity and functionality"""
    
    def __init__(self, ollama_url: str):
        """
        Initialize test with remote Ollama URL
        
        Args:
            ollama_url: Remote Ollama server URL (e.g., http://192.168.1.100:11434)
        """
        self.ollama_url = ollama_url.rstrip('/')
        self.session = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_basic_connectivity(self) -> bool:
        """Test basic HTTP connectivity to Ollama server"""
        self.log("Testing basic connectivity...")
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                self.log("✅ Basic connectivity: SUCCESS")
                return True
            else:
                self.log(f"❌ Basic connectivity failed: HTTP {response.status_code}", "ERROR")
                return False
        except requests.exceptions.ConnectTimeout:
            self.log("❌ Connection timeout - check IP address and firewall", "ERROR")
            return False
        except requests.exceptions.ConnectionError:
            self.log("❌ Connection error - server may be down or unreachable", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Unexpected error: {e}", "ERROR")
            return False
    
    def test_model_list(self) -> Optional[List[Dict]]:
        """Test retrieving model list from remote Ollama"""
        self.log("Testing model list retrieval...")
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=15)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                self.log(f"✅ Found {len(models)} models on remote server")
                
                for model in models[:5]:  # Show first 5 models
                    name = model.get('name', 'Unknown')
                    size = model.get('size', 0)
                    size_gb = size / (1024**3) if size else 0
                    self.log(f"   📦 Model: {name} ({size_gb:.2f} GB)")
                
                return models
            else:
                self.log(f"❌ Failed to get model list: HTTP {response.status_code}", "ERROR")
                return None
        except Exception as e:
            self.log(f"❌ Error getting model list: {e}", "ERROR")
            return None
    
    async def test_chat_completion(self, model_name: str = None) -> bool:
        """Test chat completion with remote Ollama"""
        if not model_name:
            # Try to get first available model
            models = self.test_model_list()
            if not models:
                self.log("❌ No models found for chat test", "ERROR")
                return False
            model_name = models[0]['name']
        
        self.log(f"Testing chat completion with model: {model_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "user", "content": "Hello, this is a connection test. Please respond with 'OK'."}
                    ],
                    "stream": False
                }
                
                async with session.post(
                    f"{self.ollama_url}/v1/chat/completions",
                    json=payload,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                        self.log(f"✅ Chat completion successful: {content[:100]}...")
                        return True
                    else:
                        self.log(f"❌ Chat completion failed: HTTP {response.status}", "ERROR")
                        return False
        except Exception as e:
            self.log(f"❌ Chat completion error: {e}", "ERROR")
            return False
    
    def test_latency(self) -> Optional[float]:
        """Test network latency to remote Ollama server"""
        self.log("Testing network latency...")
        
        latencies = []
        for i in range(5):
            try:
                start_time = time.time()
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    latency = (end_time - start_time) * 1000  # Convert to ms
                    latencies.append(latency)
                    self.log(f"   Ping {i+1}: {latency:.2f}ms")
            except Exception as e:
                self.log(f"   Ping {i+1}: Failed - {e}")
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            self.log(f"✅ Average latency: {avg_latency:.2f}ms")
            
            if avg_latency < 50:
                self.log("   🟢 Excellent latency (< 50ms)")
            elif avg_latency < 200:
                self.log("   🟡 Good latency (< 200ms)")
            else:
                self.log("   🔴 High latency (> 200ms) - consider optimizing network")
            
            return avg_latency
        else:
            self.log("❌ All latency tests failed", "ERROR")
            return None
    
    def generate_config_snippet(self, ollama_url: str) -> str:
        """Generate configuration snippet for remote Ollama"""
        return f"""
# Configuration snippet for your openai-forward-config.yaml:

forward:
  # ... other services ...
  
  # Remote Ollama Server Configuration
  - base_url: "{ollama_url}"
    route: "/ollama"
    type: "general"
    timeout: 60

# Environment variable for docker-compose:
OLLAMA_REMOTE_URL={ollama_url}
"""

    async def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        self.log("🚀 Starting comprehensive remote Ollama test...")
        self.log(f"Target server: {self.ollama_url}")
        self.log("=" * 60)
        
        results = {
            'connectivity': False,
            'model_list': False,
            'chat_completion': False,
            'latency': False
        }
        
        # Test 1: Basic connectivity
        results['connectivity'] = self.test_basic_connectivity()
        if not results['connectivity']:
            self.log("❌ Basic connectivity failed - stopping tests", "ERROR")
            return results
        
        # Test 2: Model list
        models = self.test_model_list()
        results['model_list'] = models is not None
        
        # Test 3: Network latency
        latency = self.test_latency()
        results['latency'] = latency is not None
        
        # Test 4: Chat completion (if models available)
        if models:
            results['chat_completion'] = await self.test_chat_completion(models[0]['name'])
        
        self.log("=" * 60)
        self.log("🎯 TEST SUMMARY:")
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            self.log(f"   {test_name.replace('_', ' ').title()}: {status}")
        
        all_passed = all(results.values())
        if all_passed:
            self.log("🎉 All tests passed! Remote Ollama is ready for use.")
            self.log(self.generate_config_snippet(self.ollama_url))
        else:
            self.log("⚠️  Some tests failed. Please check your remote Ollama configuration.")
        
        return results


async def main():
    """Main test function"""
    if len(sys.argv) != 2:
        print("Usage: python test_remote_ollama.py <remote_ollama_url>")
        print("Example: python test_remote_ollama.py http://192.168.1.100:11434")
        sys.exit(1)
    
    ollama_url = sys.argv[1]
    
    # Validate URL format
    if not ollama_url.startswith(('http://', 'https://')):
        print("❌ Error: URL must start with http:// or https://")
        sys.exit(1)
    
    # Run tests
    tester = RemoteOllamaTest(ollama_url)
    results = await tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    # Install required packages if not available
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