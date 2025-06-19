#!/usr/bin/env python3

# ==============================================================================
# OpenAI Forward Multi-AI Provider Test Script
# ==============================================================================
# Description: Test script for validating DeepSeek and LingyiWanwu API integration
# Author: Assistant
# Created: 2024-12-19
# Version: 1.0
#
# This script provides:
# - Automated testing of both AI providers
# - Error handling and logging with timestamps
# - OpenAI-compatible interface validation
# - Performance measurement and reporting
# ==============================================================================

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class AIProviderTester:
    """Test multiple AI providers through OpenAI Forward proxy"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the tester with base URL
        
        Args:
            base_url: Base URL of the OpenAI Forward service
        """
        self.base_url = base_url
        self.session = requests.Session()
        logger.info(f"Initialized AI Provider Tester with base URL: {base_url}")
    
    def test_api_endpoint(
        self, 
        endpoint: str, 
        api_key: str, 
        model: str, 
        message: str,
        provider_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Test a specific AI API endpoint with error handling
        
        Args:
            endpoint: API endpoint path
            api_key: API key for authentication
            model: Model name to use
            message: Test message to send
            provider_name: Name of the provider for logging
            
        Returns:
            Response data or None if failed
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ],
            "max_tokens": 100
        }
        
        try:
            logger.info(f"Testing {provider_name} API...")
            logger.info(f"Endpoint: {url}")
            logger.info(f"Model: {model}")
            
            start_time = time.time()
            
            response = self.session.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ {provider_name} API test successful!")
                logger.info(f"Response time: {response_time:.2f} seconds")
                logger.info(f"Model used: {data.get('model', 'Unknown')}")
                logger.info(f"Total tokens: {data.get('usage', {}).get('total_tokens', 'Unknown')}")
                
                # Extract and log the response content
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']
                    logger.info(f"Response: {content[:100]}{'...' if len(content) > 100 else ''}")
                
                return data
            else:
                logger.error(f"❌ {provider_name} API test failed!")
                logger.error(f"Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ {provider_name} API test timed out after 30 seconds")
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Failed to connect to {provider_name} API")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ {provider_name} API test failed: {str(e)}")
        except json.JSONDecodeError:
            logger.error(f"❌ {provider_name} API returned invalid JSON")
        except Exception as e:
            logger.error(f"❌ Unexpected error testing {provider_name} API: {str(e)}")
        
        return None
    
    def run_all_tests(self) -> Dict[str, bool]:
        """
        Run tests for all configured AI providers
        
        Returns:
            Dictionary of test results
        """
        logger.info("="*60)
        logger.info("Starting OpenAI Forward Multi-AI Provider Tests")
        logger.info(f"Test started at: {datetime.now()}")
        logger.info("="*60)
        
        results = {}
        
        # Test DeepSeek API
        deepseek_result = self.test_api_endpoint(
            endpoint="/deepseek/v1/chat/completions",
            api_key="sk-878a5319c7b14bc48109e19315361b7f",
            model="deepseek-chat",
            message="Hello! Please introduce yourself in one sentence.",
            provider_name="DeepSeek"
        )
        results["deepseek"] = deepseek_result is not None
        
        logger.info("-" * 40)
        
        # Test LingyiWanwu API  
        lingyiwanwu_result = self.test_api_endpoint(
            endpoint="/lingyiwanwu/v1/chat/completions",
            api_key="72ebf8a6191e45bab0f646659c8cb121",
            model="yi-34b-chat",
            message="你好！请用一句话介绍你自己。",
            provider_name="LingyiWanwu"
        )
        results["lingyiwanwu"] = lingyiwanwu_result is not None
        
        # Print summary
        logger.info("="*60)
        logger.info("Test Summary:")
        logger.info(f"DeepSeek API: {'✅ PASSED' if results['deepseek'] else '❌ FAILED'}")
        logger.info(f"LingyiWanwu API: {'✅ PASSED' if results['lingyiwanwu'] else '❌ FAILED'}")
        
        success_count = sum(results.values())
        total_count = len(results)
        logger.info(f"Overall: {success_count}/{total_count} tests passed")
        logger.info("="*60)
        
        return results


def main():
    """Main function to run the AI provider tests"""
    try:
        tester = AIProviderTester()
        results = tester.run_all_tests()
        
        # Exit with appropriate code
        if all(results.values()):
            logger.info("🎉 All tests passed successfully!")
            exit(0)
        else:
            logger.error("⚠️  Some tests failed. Please check the logs above.")
            exit(1)
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during testing: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()

# ==============================================================================
# Usage Examples:
#
# Run all tests:
#   python3 test_apis.py
#
# Requirements:
#   pip install requests
# ============================================================================== 