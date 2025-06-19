#!/usr/bin/env python3

# ==============================================================================
# AI Router Test Script
# ==============================================================================
# Description: Comprehensive testing script for Smart AI Router
# Author: Assistant
# Created: 2024-12-19
# Version: 1.0
#
# This script tests:
# - Unified API endpoint functionality
# - Provider health checking
# - Load balancing and failover
# - Statistics and monitoring
# ==============================================================================

import json
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Any

import httpx

# Configure logging with timestamp
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ai_router_test")

class AIRouterTester:
    """Comprehensive tester for Smart AI Router"""
    
    def __init__(self, base_url: str = "http://localhost:9000"):
        """Initialize the tester with base URL"""
        self.base_url = base_url
        self.api_key = "sk-router-2024-unified-api-key"  # 统一API密钥
        self.client = httpx.Client(timeout=60.0)
        self.test_results = []
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", response_time: float = 0):
        """Log test results"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name} ({response_time:.2f}s) - {details}")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def test_health_check(self) -> bool:
        """Test health check endpoint"""
        try:
            start_time = time.time()
            response = self.client.get(f"{self.base_url}/health")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_test_result(
                    "Health Check",
                    True,
                    f"Status: {data.get('status', 'unknown')}",
                    response_time
                )
                return True
            else:
                self.log_test_result(
                    "Health Check",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_test_result("Health Check", False, f"Exception: {str(e)}", 0)
            return False
    
    def test_stats_endpoint(self) -> bool:
        """Test statistics endpoint"""
        try:
            start_time = time.time()
            response = self.client.get(f"{self.base_url}/stats")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get('stats', {})
                providers = data.get('providers', [])
                
                self.log_test_result(
                    "Statistics Endpoint",
                    True,
                    f"Total requests: {stats.get('total_requests', 0)}, Providers: {len(providers)}",
                    response_time
                )
                return True
            else:
                self.log_test_result(
                    "Statistics Endpoint",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_test_result("Statistics Endpoint", False, f"Exception: {str(e)}", 0)
            return False
    
    def test_chat_completion(self, model: str = "gpt-3.5-turbo", message: str = "Hello! Please respond with a short greeting.") -> bool:
        """Test chat completion with specific model"""
        try:
            start_time = time.time()
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                "max_tokens": 50,
                "temperature": 0.7
            }
            
            response = self.client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.get_auth_headers(),
                json=payload
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                choices = data.get('choices', [])
                router_info = data.get('_router_info', {})
                
                if choices and len(choices) > 0:
                    content = choices[0].get('message', {}).get('content', '')
                    provider = router_info.get('provider', 'unknown')
                    
                    self.log_test_result(
                        f"Chat Completion ({model})",
                        True,
                        f"Provider: {provider}, Response: {content[:50]}...",
                        response_time
                    )
                    return True
                else:
                    self.log_test_result(
                        f"Chat Completion ({model})",
                        False,
                        "No choices in response",
                        response_time
                    )
                    return False
            else:
                self.log_test_result(
                    f"Chat Completion ({model})",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log_test_result(f"Chat Completion ({model})", False, f"Exception: {str(e)}", 0)
            return False
    
    def test_model_mapping(self) -> bool:
        """Test different model name mappings"""
        models_to_test = [
            "gpt-3.5-turbo",
            "gpt-4", 
            "code-assistant",
            "deepseek-chat",
            "yi-34b-chat"
        ]
        
        success_count = 0
        total_tests = len(models_to_test)
        
        for model in models_to_test:
            if self.test_chat_completion(model, f"Test message for model {model}"):
                success_count += 1
        
        success_rate = success_count / total_tests
        self.log_test_result(
            "Model Mapping Test",
            success_rate >= 0.5,  # At least 50% success rate
            f"Success rate: {success_rate:.1%} ({success_count}/{total_tests})",
            0
        )
        
        return success_rate >= 0.5
    
    def test_load_balancing(self, num_requests: int = 5) -> bool:
        """Test load balancing by making multiple requests"""
        providers_used = set()
        success_count = 0
        
        for i in range(num_requests):
            try:
                start_time = time.time()
                
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Test request #{i+1} for load balancing"
                        }
                    ],
                    "max_tokens": 20
                }
                
                response = self.client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=self.get_auth_headers(),
                    json=payload
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    router_info = data.get('_router_info', {})
                    provider = router_info.get('provider', 'unknown')
                    providers_used.add(provider)
                    success_count += 1
                    
                    logger.info(f"Request {i+1}: Provider {provider} ({response_time:.2f}s)")
                else:
                    logger.warning(f"Request {i+1} failed: HTTP {response.status_code}")
                
                # Small delay between requests
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Request {i+1} error: {str(e)}")
        
        success_rate = success_count / num_requests
        providers_count = len(providers_used)
        
        self.log_test_result(
            "Load Balancing Test",
            success_rate >= 0.8 and providers_count > 0,
            f"Success rate: {success_rate:.1%}, Providers used: {providers_count} ({list(providers_used)})",
            0
        )
        
        return success_rate >= 0.8 and providers_count > 0
    
    def test_error_handling(self) -> bool:
        """Test error handling with invalid requests"""
        test_cases = [
            {
                "name": "Invalid Model",
                "payload": {
                    "model": "invalid-model-name",
                    "messages": [{"role": "user", "content": "test"}]
                },
                "expected_status": [400, 404, 422, 500]
            },
            {
                "name": "Missing Messages",
                "payload": {
                    "model": "gpt-3.5-turbo"
                },
                "expected_status": [400, 422]
            },
            {
                "name": "Invalid Message Format",
                "payload": {
                    "model": "gpt-3.5-turbo",
                    "messages": "invalid"
                },
                "expected_status": [400, 422]
            }
        ]
        
        success_count = 0
        total_tests = len(test_cases)
        
        for test_case in test_cases:
            try:
                start_time = time.time()
                
                response = self.client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=self.get_auth_headers(),
                    json=test_case["payload"]
                )
                
                response_time = time.time() - start_time
                
                if response.status_code in test_case["expected_status"]:
                    self.log_test_result(
                        f"Error Handling - {test_case['name']}",
                        True,
                        f"Expected error status: {response.status_code}",
                        response_time
                    )
                    success_count += 1
                else:
                    self.log_test_result(
                        f"Error Handling - {test_case['name']}",
                        False,
                        f"Unexpected status: {response.status_code}",
                        response_time
                    )
                    
            except Exception as e:
                self.log_test_result(
                    f"Error Handling - {test_case['name']}",
                    False,
                    f"Exception: {str(e)}",
                    0
                )
        
        success_rate = success_count / total_tests
        return success_rate >= 0.8
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        logger.info("🚀 Starting AI Router comprehensive test suite...")
        start_time = time.time()
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("Statistics Endpoint", self.test_stats_endpoint),
            ("Basic Chat Completion", lambda: self.test_chat_completion()),
            ("Model Mapping", self.test_model_mapping),
            ("Load Balancing", self.test_load_balancing),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"🔍 Running {test_name}...")
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                logger.error(f"❌ Test {test_name} crashed: {str(e)}")
        
        total_time = time.time() - start_time
        success_rate = passed_tests / total_tests
        
        # Summary
        logger.info(f"\n{'='*50}")
        logger.info(f"🎯 TEST SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {success_rate:.1%}")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info(f"{'='*50}")
        
        if success_rate >= 0.8:
            logger.info("🎉 AI Router is working correctly!")
        elif success_rate >= 0.5:
            logger.warning("⚠️ AI Router has some issues but is partially functional")
        else:
            logger.error("❌ AI Router has significant issues")
        
        return {
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "total_time": total_time,
            "test_results": self.test_results
        }

def main():
    """Main function to run AI Router tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Smart AI Router")
    parser.add_argument("--url", default="http://localhost:9000", help="AI Router base URL")
    parser.add_argument("--output", help="Output file for test results (JSON)")
    
    args = parser.parse_args()
    
    tester = AIRouterTester(args.url)
    results = tester.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"📄 Test results saved to {args.output}")

if __name__ == "__main__":
    main() 