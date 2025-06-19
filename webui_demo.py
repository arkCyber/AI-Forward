#!/usr/bin/env python3
# ==============================================================================
# OpenAI Forward WebUI Demonstration Script
# ==============================================================================
# Description: Demonstration script for WebUI functionality and usage
# Author: Assistant
# Created: 2024-12-19
# Version: 1.0
#
# Features:
# - WebUI service management
# - Configuration testing
# - API endpoint validation
# - Usage examples
# ==============================================================================

import os
import sys
import time
import json
import logging
import requests
import subprocess
from datetime import datetime
from typing import Dict, Optional

# Configure logging with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class WebUIDemo:
    """
    Demonstration class for OpenAI Forward WebUI functionality.
    
    This class provides methods to demonstrate WebUI features,
    test configuration management, and show usage examples.
    """
    
    def __init__(self):
        """Initialize the demo with default configuration."""
        self.webui_url = 'http://localhost:8001'
        self.api_url = 'http://localhost:8000'
        self.timeout = 30
        logger.info("WebUI Demo initialized with timestamp: %s", 
                   datetime.now().isoformat())
    
    def check_webui_status(self) -> bool:
        """
        Check if the WebUI is running and accessible.
        
        Returns:
            bool: True if WebUI is accessible, False otherwise
        """
        try:
            response = requests.get(f"{self.webui_url}/_stcore/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ WebUI is running and healthy")
                return True
            else:
                logger.error("❌ WebUI health check failed (status: %s)", response.status_code)
                return False
        except requests.exceptions.ConnectionError:
            logger.error("❌ WebUI is not accessible - service may not be running")
            return False
        except Exception as e:
            logger.error("❌ Error checking WebUI status: %s", str(e))
            return False
    
    def check_api_status(self) -> bool:
        """
        Check if the OpenAI Forward API is running.
        
        Returns:
            bool: True if API is accessible, False otherwise
        """
        try:
            response = requests.get(f"{self.api_url}/healthz", timeout=10)
            if response.status_code == 200:
                logger.info("✅ OpenAI Forward API is running and healthy")
                return True
            else:
                logger.error("❌ API health check failed (status: %s)", response.status_code)
                return False
        except requests.exceptions.ConnectionError:
            logger.error("❌ OpenAI Forward API is not accessible")
            return False
        except Exception as e:
            logger.error("❌ Error checking API status: %s", str(e))
            return False
    
    def start_webui_service(self) -> bool:
        """
        Start the WebUI service if it's not running.
        
        Returns:
            bool: True if service started successfully, False otherwise
        """
        if self.check_webui_status():
            logger.info("WebUI is already running")
            return True
        
        try:
            logger.info("🚀 Starting WebUI service...")
            
            # Start the WebUI service in the background
            process = subprocess.Popen(
                [
                    'python', '-m', 'openai_forward.__main__', 
                    'run', '--webui', '--port', '8000', '--ui_port', '8001'
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for the service to start
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                if self.check_webui_status():
                    logger.info("✅ WebUI service started successfully")
                    return True
                logger.info(f"⏳ Waiting for WebUI to start... ({i+1}/30)")
            
            logger.error("❌ WebUI service failed to start within 30 seconds")
            return False
            
        except Exception as e:
            logger.error("❌ Error starting WebUI service: %s", str(e))
            return False
    
    def demonstrate_webui_features(self):
        """Demonstrate the main WebUI features and capabilities."""
        logger.info("🎯 Demonstrating WebUI Features")
        logger.info("=" * 60)
        
        # Check service status
        webui_running = self.check_webui_status()
        api_running = self.check_api_status()
        
        if not webui_running:
            logger.info("Starting WebUI service...")
            if not self.start_webui_service():
                logger.error("Failed to start WebUI service")
                return
        
        # Display access information
        logger.info("🌐 WebUI Access Information:")
        logger.info(f"   WebUI URL: {self.webui_url}")
        logger.info(f"   API URL: {self.api_url}")
        logger.info("")
        
        # Test WebUI endpoints
        self.test_webui_endpoints()
        
        # Show configuration examples
        self.show_configuration_examples()
        
        # Display usage instructions
        self.show_usage_instructions()
    
    def test_webui_endpoints(self):
        """Test various WebUI endpoints to verify functionality."""
        logger.info("🔍 Testing WebUI Endpoints:")
        
        endpoints = {
            'Health Check': '/_stcore/health',
            'Main Page': '/',
            'Static Assets': '/static/css/bootstrap.min.css'
        }
        
        for name, endpoint in endpoints.items():
            try:
                url = f"{self.webui_url}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"   ✅ {name}: OK (status: {response.status_code})")
                else:
                    logger.warning(f"   ⚠️  {name}: Warning (status: {response.status_code})")
                    
            except Exception as e:
                logger.error(f"   ❌ {name}: Error - {str(e)}")
        
        logger.info("")
    
    def show_configuration_examples(self):
        """Show examples of configuration management through WebUI."""
        logger.info("⚙️  Configuration Management Examples:")
        logger.info("   The WebUI provides the following configuration sections:")
        logger.info("   • Forward Configuration - Set up API forwarding rules")
        logger.info("   • API Key & Level Management - Configure access control")
        logger.info("   • Cache Settings - Configure response caching")
        logger.info("   • Rate Limiting - Set up request rate controls")
        logger.info("   • Real-time Logs - Monitor system activity")
        logger.info("   • Playground - Test API endpoints")
        logger.info("   • Statistics - View usage analytics")
        logger.info("")
    
    def show_usage_instructions(self):
        """Display detailed usage instructions for the WebUI."""
        logger.info("📖 WebUI Usage Instructions:")
        logger.info("=" * 60)
        logger.info("")
        logger.info("1. 🌐 Access the WebUI:")
        logger.info(f"   Open your browser and navigate to: {self.webui_url}")
        logger.info("")
        logger.info("2. 🔧 Configure Services:")
        logger.info("   • Use the sidebar to navigate between configuration sections")
        logger.info("   • Modify settings using the interactive forms")
        logger.info("   • Click 'Apply and Restart' to save changes")
        logger.info("")
        logger.info("3. 📊 Monitor Activity:")
        logger.info("   • Check 'Real-time Logs' for system activity")
        logger.info("   • View 'Statistics' for usage analytics")
        logger.info("   • Use 'Playground' to test API endpoints")
        logger.info("")
        logger.info("4. 🚀 API Usage:")
        logger.info(f"   • Main API endpoint: {self.api_url}")
        logger.info("   • Health check: {}/healthz".format(self.api_url))
        logger.info("   • Chat completions: {}/v1/chat/completions".format(self.api_url))
        logger.info("")
        logger.info("5. 🐳 Docker Integration:")
        logger.info("   • Build WebUI image: docker build -f webui.Dockerfile -t openai-forward-webui .")
        logger.info("   • Run with docker-compose: docker-compose up openai-forward-webui -d")
        logger.info("   • View logs: docker-compose logs -f openai-forward-webui")
        logger.info("")
    
    def test_api_integration(self):
        """Test the integration between WebUI and API services."""
        logger.info("🔗 Testing API Integration:")
        
        # Test basic API endpoints
        test_endpoints = [
            ('/healthz', 'Health Check'),
            ('/v1/models', 'Models List'),
        ]
        
        for endpoint, description in test_endpoints:
            try:
                url = f"{self.api_url}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"   ✅ {description}: OK")
                else:
                    logger.warning(f"   ⚠️  {description}: Status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"   ❌ {description}: Error - {str(e)}")
        
        logger.info("")
    
    def run_demo(self):
        """Run the complete WebUI demonstration."""
        try:
            logger.info("🎉 Starting OpenAI Forward WebUI Demonstration")
            logger.info("=" * 60)
            logger.info("")
            
            # Run the demonstration
            self.demonstrate_webui_features()
            self.test_api_integration()
            
            logger.info("✨ Demonstration completed successfully!")
            logger.info("")
            logger.info("🎯 Next Steps:")
            logger.info("   1. Open your browser and visit: {}".format(self.webui_url))
            logger.info("   2. Explore the configuration options")
            logger.info("   3. Test API endpoints using the playground")
            logger.info("   4. Monitor real-time logs and statistics")
            logger.info("")
            
        except KeyboardInterrupt:
            logger.info("Demo interrupted by user")
        except Exception as e:
            logger.error("Demo failed with error: %s", str(e), exc_info=True)


def main():
    """Main function to run the WebUI demonstration."""
    demo = WebUIDemo()
    demo.run_demo()


if __name__ == '__main__':
    main() 