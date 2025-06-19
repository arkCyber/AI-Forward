#!/usr/bin/env python3
# ==============================================================================
# OpenAI Forward WebUI Module Error Fix Script
# ==============================================================================
# Description: Automatic fix for WebUI module import issues
# Author: Assistant
# Created: 2024-12-19
# Version: 1.0
#
# Features:
# - Automatic detection of module import issues
# - Package installation and verification
# - WebUI service startup and testing
# ==============================================================================

import os
import sys
import subprocess
import logging
import time
from datetime import datetime
from pathlib import Path

# Configure logging with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class WebUIModuleFixer:
    """
    Automatic fixer for OpenAI Forward WebUI module import issues.
    
    This class provides methods to diagnose and fix common WebUI import problems.
    """
    
    def __init__(self):
        """Initialize the fixer with current working directory."""
        self.project_root = Path.cwd()
        self.requirements_fixed = False
        logger.info("WebUI Module Fixer initialized at: %s", self.project_root)
        logger.info("Timestamp: %s", datetime.now().isoformat())
    
    def check_module_installation(self) -> bool:
        """
        Check if openai_forward module is properly installed.
        
        Returns:
            bool: True if module is installed, False otherwise
        """
        try:
            result = subprocess.run(
                ['pip', 'show', 'openai_forward'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info("✅ openai_forward module is installed")
                logger.info("Package info: %s", result.stdout.split('\n')[0:3])
                return True
            else:
                logger.warning("❌ openai_forward module is not installed")
                return False
                
        except Exception as e:
            logger.error("Error checking module installation: %s", str(e))
            return False
    
    def install_package(self) -> bool:
        """
        Install the openai_forward package in editable mode.
        
        Returns:
            bool: True if installation successful, False otherwise
        """
        try:
            logger.info("🔧 Installing openai_forward package...")
            
            # First, ensure we have required build tools
            logger.info("Installing build dependencies...")
            subprocess.run(
                ['pip', 'install', '--upgrade', 'setuptools', 'wheel'],
                check=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Install compatible packaging version
            subprocess.run(
                ['pip', 'install', 'packaging<25,>=23.2'],
                check=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Install the main package
            result = subprocess.run(
                ['pip', 'install', '-e', '.'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                logger.info("✅ Package installation successful")
                return True
            else:
                logger.error("❌ Package installation failed")
                logger.error("Error output: %s", result.stderr)
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error("Installation command failed: %s", str(e))
            return False
        except Exception as e:
            logger.error("Error during installation: %s", str(e))
            return False
    
    def install_webui_dependencies(self) -> bool:
        """
        Install WebUI-specific dependencies.
        
        Returns:
            bool: True if installation successful, False otherwise
        """
        try:
            logger.info("🔧 Installing WebUI dependencies...")
            
            # Install streamlit with compatible version
            result = subprocess.run(
                ['pip', 'install', 'streamlit~=1.30.0'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("✅ WebUI dependencies installed successfully")
                return True
            else:
                logger.warning("⚠️ WebUI dependencies installation had issues")
                logger.warning("Error output: %s", result.stderr)
                return True  # Continue anyway as streamlit might already be installed
                
        except Exception as e:
            logger.error("Error installing WebUI dependencies: %s", str(e))
            return False
    
    def test_module_import(self) -> bool:
        """
        Test if the openai_forward module can be imported successfully.
        
        Returns:
            bool: True if import successful, False otherwise
        """
        try:
            # Test basic module import
            result = subprocess.run(
                [sys.executable, '-c', 'import openai_forward; print("Import successful")'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info("✅ Module import test successful")
                return True
            else:
                logger.error("❌ Module import test failed")
                logger.error("Error: %s", result.stderr)
                return False
                
        except Exception as e:
            logger.error("Error testing module import: %s", str(e))
            return False
    
    def start_webui_service(self) -> bool:
        """
        Start the WebUI service and verify it's running.
        
        Returns:
            bool: True if service started successfully, False otherwise
        """
        try:
            logger.info("🚀 Starting WebUI service...")
            
            # Start the service in the background
            process = subprocess.Popen(
                [
                    sys.executable, '-m', 'openai_forward.__main__',
                    'run', '--webui', '--port', '8000', '--ui_port', '8001'
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for service to start
            max_wait = 30
            for i in range(max_wait):
                time.sleep(1)
                
                # Test if service is responsive
                try:
                    import requests
                    response = requests.get('http://localhost:8001/_stcore/health', timeout=5)
                    if response.status_code == 200:
                        logger.info("✅ WebUI service started successfully")
                        logger.info("WebUI accessible at: http://localhost:8001")
                        logger.info("API accessible at: http://localhost:8000")
                        return True
                except:
                    pass
                
                if i % 5 == 0:
                    logger.info(f"⏳ Waiting for service to start... ({i+1}/{max_wait})")
            
            logger.error("❌ WebUI service failed to start within %d seconds", max_wait)
            process.terminate()
            return False
            
        except Exception as e:
            logger.error("Error starting WebUI service: %s", str(e))
            return False
    
    def run_fix_process(self) -> bool:
        """
        Run the complete fix process for WebUI module issues.
        
        Returns:
            bool: True if all fixes successful, False otherwise
        """
        logger.info("🔧 Starting WebUI Module Fix Process")
        logger.info("=" * 60)
        
        # Step 1: Check current installation
        if self.check_module_installation():
            logger.info("Module is already installed, testing import...")
            if self.test_module_import():
                logger.info("Module import successful, testing WebUI...")
                # Try to start WebUI directly
                if self.start_webui_service():
                    return True
        
        # Step 2: Install package if needed
        if not self.install_package():
            logger.error("Failed to install package")
            return False
        
        # Step 3: Install WebUI dependencies
        if not self.install_webui_dependencies():
            logger.error("Failed to install WebUI dependencies")
            return False
        
        # Step 4: Test module import
        if not self.test_module_import():
            logger.error("Module import still failing after installation")
            return False
        
        # Step 5: Start WebUI service
        if not self.start_webui_service():
            logger.error("Failed to start WebUI service")
            return False
        
        logger.info("✨ All fixes applied successfully!")
        return True
    
    def generate_fix_report(self, success: bool):
        """
        Generate a summary report of the fix process.
        
        Args:
            success (bool): Whether the fix process was successful
        """
        report_lines = [
            "=" * 60,
            "OpenAI Forward WebUI Module Fix Report",
            "=" * 60,
            f"Timestamp: {datetime.now().isoformat()}",
            f"Project Root: {self.project_root}",
            f"Fix Status: {'SUCCESS' if success else 'FAILED'}",
            ""
        ]
        
        if success:
            report_lines.extend([
                "✅ Fix Results:",
                "   • openai_forward module installed successfully",
                "   • WebUI dependencies installed",
                "   • Module import test passed",
                "   • WebUI service started successfully",
                "",
                "🌐 Access Points:",
                "   • WebUI: http://localhost:8001",
                "   • API: http://localhost:8000",
                "   • Health: http://localhost:8001/_stcore/health",
                "",
                "🎯 Next Steps:",
                "   1. Open your browser to http://localhost:8001",
                "   2. Test configuration management features",
                "   3. Monitor real-time logs and statistics",
            ])
        else:
            report_lines.extend([
                "❌ Fix Failed:",
                "   Some issues could not be resolved automatically.",
                "",
                "🔧 Manual Steps to Try:",
                "   1. Check Python environment and virtual environment",
                "   2. Manually run: pip install -e .",
                "   3. Verify all dependencies are installed",
                "   4. Check for conflicting package versions",
                "",
                "📞 Support:",
                "   • Check project documentation",
                "   • Open GitHub issue with error details",
            ])
        
        report_lines.extend([
            "",
            "=" * 60
        ])
        
        report = '\n'.join(report_lines)
        print("\n" + report)
        
        # Save report to file
        try:
            report_file = f"webui_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info("📄 Fix report saved to: %s", report_file)
        except Exception as e:
            logger.warning("Could not save report file: %s", str(e))


def main():
    """Main function to run the WebUI module fixer."""
    try:
        logger.info("🚀 OpenAI Forward WebUI Module Error Fix")
        logger.info("Starting automatic diagnosis and repair...")
        
        fixer = WebUIModuleFixer()
        success = fixer.run_fix_process()
        fixer.generate_fix_report(success)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Fix process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error("Fix process failed with error: %s", str(e), exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main() 