#!/usr/bin/env python3
# ==============================================================================
# OpenAI Forward WebUI Docker Integration Test Suite
# ==============================================================================
# Description: Comprehensive test script for WebUI Docker functionality
# Author: Assistant
# Created: 2024-12-19
# Version: 1.0
#
# Features:
# - Docker service health checks
# - WebUI accessibility testing
# - API endpoint validation
# - Configuration management testing
# - Logging verification
# ==============================================================================

import os
import sys
import time
import json
import logging
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configure logging with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'webui_docker_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class WebUIDockerTester:
    """
    Comprehensive tester for OpenAI Forward WebUI Docker integration.
    
    This class provides methods to test Docker services, WebUI functionality,
    API endpoints, and overall system integration.
    """
    
    def __init__(self):
        """Initialize the tester with default configuration."""
        self.services = {
            'openai-forward': {'port': 8000, 'health_endpoint': '/healthz'},
            'openai-forward-webui': {'port': 8001, 'health_endpoint': '/_stcore/health'},
            'ollama': {'port': 11434, 'health_endpoint': '/api/version'},
            'ai-router': {'port': 9000, 'health_endpoint': '/health'}
        }
        self.base_url = 'http://localhost'
        self.timeout = 30
        logger.info("WebUI Docker Tester initialized with timestamp: %s", 
                   datetime.now().isoformat())
    
    def check_docker_status(self) -> bool:
        """
        Check if Docker is running and accessible.
        
        Returns:
            bool: True if Docker is running, False otherwise
        """
        try:
            result = subprocess.run(
                ['docker', 'ps'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                logger.info("Docker is running successfully")
                return True
            else:
                logger.error("Docker command failed: %s", result.stderr)
                return False
        except subprocess.TimeoutExpired:
            logger.error("Docker status check timed out")
            return False
        except FileNotFoundError:
            logger.error("Docker command not found - is Docker installed?")
            return False
        except Exception as e:
            logger.error("Error checking Docker status: %s", str(e))
            return False
    
    def check_service_health(self, service_name: str) -> Tuple[bool, str]:
        """
        Check the health status of a specific service.
        
        Args:
            service_name (str): Name of the service to check
            
        Returns:
            Tuple[bool, str]: (is_healthy, status_message)
        """
        if service_name not in self.services:
            error_msg = f"Unknown service: {service_name}"
            logger.error(error_msg)
            return False, error_msg
        
        service_config = self.services[service_name]
        url = f"{self.base_url}:{service_config['port']}{service_config['health_endpoint']}"
        
        try:
            logger.info("Checking health for %s at %s", service_name, url)
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                success_msg = f"{service_name} is healthy (status: {response.status_code})"
                logger.info(success_msg)
                return True, success_msg
            else:
                error_msg = f"{service_name} health check failed (status: {response.status_code})"
                logger.warning(error_msg)
                return False, error_msg
                
        except requests.exceptions.ConnectionError as e:
            error_msg = f"{service_name} connection failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except requests.exceptions.Timeout as e:
            error_msg = f"{service_name} health check timed out: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"{service_name} health check error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def test_webui_accessibility(self) -> Tuple[bool, str]:
        """
        Test if the WebUI is accessible and responding correctly.
        
        Returns:
            Tuple[bool, str]: (is_accessible, status_message)
        """
        webui_url = f"{self.base_url}:8001"
        
        try:
            logger.info("Testing WebUI accessibility at %s", webui_url)
            response = requests.get(webui_url, timeout=self.timeout)
            
            if response.status_code == 200:
                # Check if the response contains Streamlit-specific content
                content = response.text.lower()
                if 'streamlit' in content or 'openai forward' in content:
                    success_msg = "WebUI is accessible and contains expected content"
                    logger.info(success_msg)
                    return True, success_msg
                else:
                    warning_msg = "WebUI accessible but content may be incomplete"
                    logger.warning(warning_msg)
                    return True, warning_msg
            else:
                error_msg = f"WebUI accessibility test failed (status: {response.status_code})"
                logger.warning(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"WebUI accessibility test error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def test_api_endpoints(self) -> Dict[str, Tuple[bool, str]]:
        """
        Test various API endpoints for functionality.
        
        Returns:
            Dict[str, Tuple[bool, str]]: Results for each endpoint tested
        """
        endpoints_to_test = {
            'openai_forward_health': f"{self.base_url}:8000/healthz",
            'ai_router_health': f"{self.base_url}:9000/health",
            'ai_router_stats': f"{self.base_url}:9000/stats",
            'ollama_version': f"{self.base_url}:11434/api/version"
        }
        
        results = {}
        
        for endpoint_name, url in endpoints_to_test.items():
            try:
                logger.info("Testing endpoint: %s", endpoint_name)
                response = requests.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    success_msg = f"{endpoint_name} responded successfully"
                    logger.info(success_msg)
                    results[endpoint_name] = (True, success_msg)
                else:
                    error_msg = f"{endpoint_name} failed (status: {response.status_code})"
                    logger.warning(error_msg)
                    results[endpoint_name] = (False, error_msg)
                    
            except Exception as e:
                error_msg = f"{endpoint_name} test error: {str(e)}"
                logger.error(error_msg)
                results[endpoint_name] = (False, error_msg)
        
        return results
    
    def check_docker_containers(self) -> Dict[str, Tuple[bool, str]]:
        """
        Check the status of Docker containers for all services.
        
        Returns:
            Dict[str, Tuple[bool, str]]: Container status for each service
        """
        results = {}
        
        try:
            # Get container status
            result = subprocess.run(
                ['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                container_info = result.stdout
                logger.info("Docker containers status:\n%s", container_info)
                
                # Check each expected container
                expected_containers = [
                    'openai-forward-proxy',
                    'openai-forward-webui', 
                    'ollama-server',
                    'smart-ai-router'
                ]
                
                for container in expected_containers:
                    if container in container_info:
                        if 'Up' in container_info:
                            success_msg = f"Container {container} is running"
                            logger.info(success_msg)
                            results[container] = (True, success_msg)
                        else:
                            error_msg = f"Container {container} found but not running"
                            logger.warning(error_msg)
                            results[container] = (False, error_msg)
                    else:
                        error_msg = f"Container {container} not found"
                        logger.warning(error_msg)
                        results[container] = (False, error_msg)
            else:
                error_msg = f"Failed to get container status: {result.stderr}"
                logger.error(error_msg)
                results['docker_ps'] = (False, error_msg)
                
        except Exception as e:
            error_msg = f"Error checking container status: {str(e)}"
            logger.error(error_msg)
            results['docker_check'] = (False, error_msg)
        
        return results
    
    def run_comprehensive_test(self) -> Dict[str, any]:
        """
        Run all tests and return comprehensive results.
        
        Returns:
            Dict[str, any]: Complete test results with timestamps
        """
        test_start_time = datetime.now()
        logger.info("Starting comprehensive WebUI Docker test at %s", 
                   test_start_time.isoformat())
        
        results = {
            'test_start_time': test_start_time.isoformat(),
            'docker_status': {},
            'container_status': {},
            'service_health': {},
            'webui_accessibility': {},
            'api_endpoints': {},
            'summary': {}
        }
        
        # Test Docker status
        docker_running = self.check_docker_status()
        results['docker_status'] = {
            'running': docker_running,
            'timestamp': datetime.now().isoformat()
        }
        
        if not docker_running:
            logger.error("Docker is not running - skipping container tests")
            results['summary'] = {
                'total_tests': 1,
                'passed': 0,
                'failed': 1,
                'overall_status': 'FAILED',
                'message': 'Docker is not running'
            }
            return results
        
        # Test container status
        container_results = self.check_docker_containers()
        results['container_status'] = container_results
        
        # Test service health
        service_results = {}
        for service_name in self.services.keys():
            is_healthy, message = self.check_service_health(service_name)
            service_results[service_name] = {
                'healthy': is_healthy,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
        results['service_health'] = service_results
        
        # Test WebUI accessibility
        webui_accessible, webui_message = self.test_webui_accessibility()
        results['webui_accessibility'] = {
            'accessible': webui_accessible,
            'message': webui_message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Test API endpoints
        api_results = self.test_api_endpoints()
        formatted_api_results = {}
        for endpoint, (success, message) in api_results.items():
            formatted_api_results[endpoint] = {
                'success': success,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
        results['api_endpoints'] = formatted_api_results
        
        # Calculate summary
        total_tests = 0
        passed_tests = 0
        
        # Count container tests
        for result in container_results.values():
            total_tests += 1
            if result[0]:
                passed_tests += 1
        
        # Count service health tests
        for service_data in service_results.values():
            total_tests += 1
            if service_data['healthy']:
                passed_tests += 1
        
        # Count WebUI test
        total_tests += 1
        if webui_accessible:
            passed_tests += 1
        
        # Count API endpoint tests
        for endpoint_data in formatted_api_results.values():
            total_tests += 1
            if endpoint_data['success']:
                passed_tests += 1
        
        overall_status = 'PASSED' if passed_tests == total_tests else 'PARTIAL' if passed_tests > 0 else 'FAILED'
        
        results['summary'] = {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': total_tests - passed_tests,
            'success_rate': f"{(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0%",
            'overall_status': overall_status,
            'test_duration': str(datetime.now() - test_start_time),
            'timestamp': datetime.now().isoformat()
        }
        
        # Log summary
        logger.info("Test Summary: %s/%s tests passed (%s) - Status: %s", 
                   passed_tests, total_tests, results['summary']['success_rate'], overall_status)
        
        return results
    
    def generate_test_report(self, results: Dict[str, any], output_file: str = None) -> str:
        """
        Generate a detailed test report.
        
        Args:
            results (Dict[str, any]): Test results from run_comprehensive_test
            output_file (str, optional): File to save the report to
            
        Returns:
            str: Formatted test report
        """
        report_lines = [
            "=" * 80,
            "OpenAI Forward WebUI Docker Integration Test Report",
            "=" * 80,
            f"Test Start Time: {results.get('test_start_time', 'N/A')}",
            f"Test Duration: {results.get('summary', {}).get('test_duration', 'N/A')}",
            "",
            "SUMMARY:",
            f"  Total Tests: {results.get('summary', {}).get('total_tests', 0)}",
            f"  Passed: {results.get('summary', {}).get('passed', 0)}",
            f"  Failed: {results.get('summary', {}).get('failed', 0)}",
            f"  Success Rate: {results.get('summary', {}).get('success_rate', '0%')}",
            f"  Overall Status: {results.get('summary', {}).get('overall_status', 'UNKNOWN')}",
            "",
            "DETAILED RESULTS:",
            ""
        ]
        
        # Docker status
        docker_status = results.get('docker_status', {})
        report_lines.extend([
            "Docker Status:",
            f"  Running: {docker_status.get('running', False)}",
            ""
        ])
        
        # Container status
        container_status = results.get('container_status', {})
        if container_status:
            report_lines.append("Container Status:")
            for container, (status, message) in container_status.items():
                report_lines.append(f"  {container}: {'✓' if status else '✗'} {message}")
            report_lines.append("")
        
        # Service health
        service_health = results.get('service_health', {})
        if service_health:
            report_lines.append("Service Health:")
            for service, data in service_health.items():
                status_icon = '✓' if data.get('healthy', False) else '✗'
                report_lines.append(f"  {service}: {status_icon} {data.get('message', 'N/A')}")
            report_lines.append("")
        
        # WebUI accessibility
        webui_data = results.get('webui_accessibility', {})
        if webui_data:
            status_icon = '✓' if webui_data.get('accessible', False) else '✗'
            report_lines.extend([
                "WebUI Accessibility:",
                f"  Status: {status_icon} {webui_data.get('message', 'N/A')}",
                ""
            ])
        
        # API endpoints
        api_endpoints = results.get('api_endpoints', {})
        if api_endpoints:
            report_lines.append("API Endpoints:")
            for endpoint, data in api_endpoints.items():
                status_icon = '✓' if data.get('success', False) else '✗'
                report_lines.append(f"  {endpoint}: {status_icon} {data.get('message', 'N/A')}")
            report_lines.append("")
        
        report_lines.extend([
            "=" * 80,
            f"Report generated at: {datetime.now().isoformat()}",
            "=" * 80
        ])
        
        report_content = '\n'.join(report_lines)
        
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                logger.info("Test report saved to: %s", output_file)
            except Exception as e:
                logger.error("Failed to save report to file: %s", str(e))
        
        return report_content


def main():
    """Main function to run the WebUI Docker test suite."""
    try:
        logger.info("Starting OpenAI Forward WebUI Docker Test Suite")
        
        # Initialize tester
        tester = WebUIDockerTester()
        
        # Run comprehensive tests
        results = tester.run_comprehensive_test()
        
        # Generate and display report
        report_file = f"webui_docker_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report = tester.generate_test_report(results, report_file)
        
        print("\n" + report)
        
        # Exit with appropriate code
        overall_status = results.get('summary', {}).get('overall_status', 'FAILED')
        if overall_status == 'PASSED':
            logger.info("All tests passed successfully")
            sys.exit(0)
        elif overall_status == 'PARTIAL':
            logger.warning("Some tests failed - check report for details")
            sys.exit(1)
        else:
            logger.error("Tests failed - check report for details")
            sys.exit(2)
            
    except KeyboardInterrupt:
        logger.info("Test suite interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error("Test suite failed with error: %s", str(e), exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main() 