#!/usr/bin/env python3
# ==============================================================================
# Native OpenAI Forward WebUI Launcher
# ==============================================================================
# Description: Script to properly launch the native OpenAI Forward WebUI
# Author: Assistant
# Created: 2024-12-19
# ==============================================================================

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def setup_environment():
    """Setup the Python environment for WebUI."""
    project_root = Path(__file__).parent.absolute()
    
    # Add project root to Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Set environment variables
    os.environ['PYTHONPATH'] = str(project_root)
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_PORT'] = '8001'
    os.environ['STREAMLIT_LOGGER_LEVEL'] = 'warning'
    
    print(f"✅ Environment setup completed")
    print(f"   Project root: {project_root}")
    print(f"   PYTHONPATH: {os.environ.get('PYTHONPATH')}")

def test_imports():
    """Test if all required modules can be imported."""
    try:
        print("🔍 Testing module imports...")
        
        # Test basic openai_forward import
        import openai_forward
        print(f"   ✅ openai_forward: {openai_forward.__version__}")
        
        # Test config interface import
        from openai_forward.config.interface import Config
        print("   ✅ openai_forward.config.interface imported")
        
        # Test webui modules
        from openai_forward.webui.chat import ChatData
        print("   ✅ openai_forward.webui.chat imported")
        
        from openai_forward.webui.helper import mermaid
        print("   ✅ openai_forward.webui.helper imported")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False

def start_api_server():
    """Start the API server if not already running."""
    try:
        import requests
        response = requests.get('http://localhost:8000/healthz', timeout=5)
        if response.status_code == 200:
            print("✅ API server already running at http://localhost:8000")
            return True
    except:
        pass
    
    print("🚀 Starting API server...")
    cmd = [sys.executable, '-m', 'openai_forward.__main__', 'run', '--port', '8000']
    
    # Start API server in background
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for API server to start
    for i in range(30):
        try:
            import requests
            response = requests.get('http://localhost:8000/healthz', timeout=2)
            if response.status_code == 200:
                print(f"✅ API server started successfully")
                return True
        except:
            pass
        time.sleep(1)
        print(f"   Waiting for API server... ({i+1}/30)")
    
    print("❌ Failed to start API server")
    return False

def start_webui():
    """Start the WebUI using streamlit."""
    print("🖥️ Starting native WebUI...")
    
    webui_script = Path(__file__).parent / 'openai_forward' / 'webui' / 'run.py'
    if not webui_script.exists():
        print(f"❌ WebUI script not found: {webui_script}")
        return False
    
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', str(webui_script),
        '--server.port', '8001',
        '--server.headless', 'true',
        '--logger.level', 'warning',
        '--browser.gatherUsageStats', 'false'
    ]
    
    print(f"🔧 Command: {' '.join(cmd)}")
    
    # Start WebUI
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=os.environ.copy()
        )
        
        print("⏳ Starting WebUI... (monitoring output)")
        
        # Monitor output for errors
        output_lines = []
        for line in iter(process.stdout.readline, ''):
            output_lines.append(line.strip())
            print(f"   {line.strip()}")
            
            # Check for successful startup
            if "You can now view your Streamlit app" in line:
                print("✅ WebUI started successfully!")
                break
                
            # Check for errors
            if "ModuleNotFoundError" in line or "ImportError" in line:
                print(f"❌ Import error detected: {line.strip()}")
                process.terminate()
                return False
                
            # Limit output lines to prevent spam
            if len(output_lines) > 20:
                break
        
        # Keep process running
        return process
        
    except Exception as e:
        print(f"❌ Failed to start WebUI: {e}")
        return False

def main():
    """Main function to start the native WebUI."""
    print("🚀 OpenAI Forward Native WebUI Launcher")
    print("=" * 60)
    
    # Setup environment
    setup_environment()
    
    # Test imports
    if not test_imports():
        print("❌ Import test failed. Cannot start WebUI.")
        return False
    
    # Start API server
    if not start_api_server():
        print("❌ Failed to start API server")
        return False
    
    # Start WebUI
    webui_process = start_webui()
    if not webui_process:
        print("❌ Failed to start WebUI")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Native OpenAI Forward WebUI is now running!")
    print("📱 WebUI: http://localhost:8001")
    print("🔧 API: http://localhost:8000")
    print("⚡ Press Ctrl+C to stop")
    print("=" * 60)
    
    # Keep running until interrupted
    try:
        webui_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping WebUI...")
        webui_process.terminate()
        print("✅ WebUI stopped")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 