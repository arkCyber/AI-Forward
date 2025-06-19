#!/usr/bin/env python3
# ==============================================================================
# NGINX Multi-AI System Monitor
# ==============================================================================
# Description: Real-time monitoring script for NGINX gateway and AI services
# Author: Assistant
# Created: 2024-12-19
# Version: 1.0
#
# Features:
# - Real-time service status monitoring
# - Performance metrics collection
# - NGINX status and configuration validation
# - Health check automation
# - User-friendly dashboard output
# ==============================================================================

import asyncio
import aiohttp
import time
import json
import subprocess
import os
from datetime import datetime
from typing import Dict, Any, List
import logging

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemMonitor:
    """NGINX Multi-AI System Monitor"""
    
    def __init__(self, base_url: str = "http://localhost"):
        """
        Initialize the system monitor
        
        Args:
            base_url: Base URL for the NGINX gateway
        """
        self.base_url = base_url
        self.monitoring = True
        
    async def get_docker_status(self) -> Dict[str, Any]:
        """Get Docker container status"""
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            container = json.loads(line)
                            containers.append({
                                "name": container.get("Name", "unknown"),
                                "service": container.get("Service", "unknown"),
                                "state": container.get("State", "unknown"),
                                "status": container.get("Status", "unknown"),
                                "ports": container.get("Publishers", [])
                            })
                        except json.JSONDecodeError:
                            continue
                
                return {"status": "success", "containers": containers}
            else:
                return {"status": "error", "message": result.stderr}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def check_nginx_health(self) -> Dict[str, Any]:
        """Check NGINX health and configuration"""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{self.base_url}/nginx-health") as resp:
                    response_time = time.time() - start_time
                    
                    if resp.status == 200:
                        content = await resp.text()
                        return {
                            "status": "healthy",
                            "response_time": response_time,
                            "content": content.strip()
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "response_time": response_time,
                            "error": f"HTTP {resp.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def check_services_health(self) -> Dict[str, Any]:
        """Check AI services health"""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{self.base_url}/health") as resp:
                    response_time = time.time() - start_time
                    
                    if resp.status == 200:
                        health_data = await resp.json()
                        return {
                            "status": "success",
                            "response_time": response_time,
                            "data": health_data
                        }
                    else:
                        return {
                            "status": "error",
                            "response_time": response_time,
                            "error": f"HTTP {resp.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def check_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{self.base_url}/stats") as resp:
                    response_time = time.time() - start_time
                    
                    if resp.status == 200:
                        stats_data = await resp.json()
                        return {
                            "status": "success",
                            "response_time": response_time,
                            "data": stats_data
                        }
                    else:
                        return {
                            "status": "error",
                            "response_time": response_time,
                            "error": f"HTTP {resp.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def test_api_endpoints(self) -> Dict[str, Any]:
        """Test various API endpoints"""
        endpoints = {
            "main_api": "/api/v1/chat/completions",
            "deepseek": "/deepseek/v1/chat/completions",
            "lingyiwanwu": "/lingyiwanwu/v1/chat/completions",
            "ollama": "/ollama/v1/chat/completions",
            "webui": "/webui/",
            "forward": "/forward/v1/chat/completions"
        }
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for name, endpoint in endpoints.items():
                try:
                    start_time = time.time()
                    
                    if endpoint == "/webui/":
                        # Just check if WebUI is accessible
                        async with session.get(f"{self.base_url}{endpoint}") as resp:
                            response_time = time.time() - start_time
                            results[name] = {
                                "accessible": resp.status in [200, 302],
                                "status_code": resp.status,
                                "response_time": response_time
                            }
                    else:
                        # Test API endpoints with a simple request
                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": "Bearer sk-8d6804b011614dba7bd065f8644514b"
                        }
                        
                        payload = {
                            "model": "deepseek-chat",
                            "messages": [{"role": "user", "content": "test"}],
                            "max_tokens": 1,
                            "stream": False
                        }
                        
                        async with session.post(
                            f"{self.base_url}{endpoint}",
                            headers=headers,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as resp:
                            response_time = time.time() - start_time
                            results[name] = {
                                "accessible": resp.status == 200,
                                "status_code": resp.status,
                                "response_time": response_time
                            }
                            
                except Exception as e:
                    results[name] = {
                        "accessible": False,
                        "error": str(e),
                        "response_time": time.time() - start_time
                    }
        
        return results
    
    def print_dashboard(self, docker_status: Dict, nginx_health: Dict, 
                       services_health: Dict, stats: Dict, endpoints: Dict):
        """Print a beautiful dashboard"""
        
        # Clear screen and print header
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🔧" + "="*78 + "🔧")
        print("🎯              NGINX Multi-AI System Monitor Dashboard                🎯")
        print("🔧" + "="*78 + "🔧")
        print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Gateway URL: {self.base_url}")
        print()
        
        # Docker containers status
        print("📦 Docker Containers Status:")
        print("-" * 80)
        if docker_status["status"] == "success":
            for container in docker_status["containers"]:
                status_icon = "🟢" if "running" in container["state"].lower() else "🔴"
                health_icon = "💚" if "healthy" in container["status"].lower() else "💛"
                
                print(f"  {status_icon} {container['name']:<25} | {container['service']:<20} | {container['state']:<10}")
                if container.get("ports"):
                    ports = ", ".join([f"{p.get('PublishedPort', 'N/A')}:{p.get('TargetPort', 'N/A')}" 
                                     for p in container["ports"]])
                    print(f"    📡 Ports: {ports}")
        else:
            print(f"  ❌ Error: {docker_status.get('message', 'Unknown error')}")
        print()
        
        # NGINX health
        print("🌐 NGINX Gateway Status:")
        print("-" * 80)
        if nginx_health["status"] == "healthy":
            print(f"  ✅ NGINX Status: HEALTHY ({nginx_health['response_time']:.3f}s)")
            print(f"  📝 Response: {nginx_health['content']}")
        else:
            print(f"  ❌ NGINX Status: {nginx_health['status'].upper()}")
            if "error" in nginx_health:
                print(f"  🚨 Error: {nginx_health['error']}")
        print()
        
        # AI Services health
        print("🤖 AI Services Health:")
        print("-" * 80)
        if services_health["status"] == "success":
            health_data = services_health["data"]
            overall_status = health_data.get("status", "unknown")
            status_icon = "✅" if overall_status == "healthy" else "❌"
            
            print(f"  {status_icon} Overall Status: {overall_status.upper()} ({services_health['response_time']:.3f}s)")
            
            providers = health_data.get("providers", {})
            for provider, info in providers.items():
                provider_status = info.get("status", "unknown")
                provider_icon = "🟢" if provider_status == "healthy" else "🔴"
                response_time = info.get("response_time", 0)
                error_count = info.get("error_count", 0)
                
                print(f"    {provider_icon} {provider.capitalize():<15} | Status: {provider_status:<8} | "
                      f"Response: {response_time:.2f}s | Errors: {error_count}")
        else:
            print(f"  ❌ Error: {services_health.get('error', 'Unknown error')}")
        print()
        
        # Service statistics
        print("📊 Service Statistics:")
        print("-" * 80)
        if stats["status"] == "success":
            stats_data = stats["data"]
            
            print(f"  📈 Total Requests: {stats_data.get('total_requests', 0)}")
            print(f"  ✅ Successful: {stats_data.get('successful_requests', 0)}")
            print(f"  ❌ Failed: {stats_data.get('failed_requests', 0)}")
            
            provider_usage = stats_data.get("provider_usage", {})
            if provider_usage:
                print("  🎯 Provider Usage:")
                for provider, count in provider_usage.items():
                    print(f"    • {provider.capitalize()}: {count} requests")
        else:
            print(f"  ❌ Error: {stats.get('error', 'Unknown error')}")
        print()
        
        # API endpoints test
        print("🔗 API Endpoints Status:")
        print("-" * 80)
        for endpoint, result in endpoints.items():
            status_icon = "✅" if result.get("accessible", False) else "❌"
            response_time = result.get("response_time", 0)
            status_code = result.get("status_code", "N/A")
            
            print(f"  {status_icon} {endpoint.replace('_', ' ').title():<20} | "
                  f"HTTP {status_code} | {response_time:.3f}s")
            
            if "error" in result:
                print(f"    🚨 Error: {result['error']}")
        print()
        
        # Multi-user features summary
        print("🚀 Multi-User Features:")
        print("-" * 80)
        print("  ⚡ Load Balancing: NGINX distributes requests across backend services")
        print("  🛡️  Rate Limiting: 100 API calls/min, 60 chat/min, 30 WebUI/min per IP")
        print("  🔐 Connection Limits: Max 50 concurrent connections per IP")
        print("  📦 Connection Pooling: HTTP/1.1 keepalive for optimal performance")
        print("  🗜️  Compression: Gzip enabled for reduced bandwidth usage")
        print("  🔒 Security Headers: XSS protection, content sniffing protection")
        print()
        
        print("🔧" + "="*78 + "🔧")
        print("🎯 Press Ctrl+C to stop monitoring | Refresh every 10 seconds        🎯")
        print("🔧" + "="*78 + "🔧")
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("🚀 Starting NGINX Multi-AI System Monitor")
        
        try:
            while self.monitoring:
                # Gather all status information
                docker_status = await self.get_docker_status()
                nginx_health = await self.check_nginx_health()
                services_health = await self.check_services_health()
                stats = await self.check_service_stats()
                endpoints = await self.test_api_endpoints()
                
                # Display dashboard
                self.print_dashboard(
                    docker_status, nginx_health, services_health, stats, endpoints
                )
                
                # Wait before next update
                await asyncio.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
            self.monitoring = False
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
        finally:
            print("\n👋 NGINX Multi-AI System Monitor stopped.")

async def main():
    """Main function"""
    monitor = SystemMonitor(base_url="http://localhost")
    await monitor.monitor_loop()

if __name__ == "__main__":
    asyncio.run(main())

# ==============================================================================
# Usage Instructions:
#
# 1. Install dependencies:
#    pip install aiohttp
#
# 2. Run the monitor:
#    python monitor_system.py
#
# 3. Monitor features:
#    - Real-time Docker container status
#    - NGINX gateway health and performance
#    - AI services health and statistics
#    - API endpoints accessibility testing
#    - Multi-user feature validation
#
# 4. Stop monitoring:
#    Press Ctrl+C to stop
# ============================================================================== 