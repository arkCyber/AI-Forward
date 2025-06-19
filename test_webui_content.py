#!/usr/bin/env python3
# ==============================================================================
# WebUI Content Test Script
# ==============================================================================
# Description: Test if WebUI is displaying the correct OpenAI Forward interface
# Author: Assistant
# Created: 2024-12-19
# ==============================================================================

import requests
import time
import json
from datetime import datetime

def test_webui_content():
    """Test if WebUI is displaying the correct content."""
    print(f"🔍 Testing WebUI Content at {datetime.now().isoformat()}")
    print("=" * 60)
    
    try:
        # Test basic connectivity
        print("1. Testing basic connectivity...")
        response = requests.get('http://localhost:8001', timeout=10)
        print(f"   Status: {response.status_code}")
        
        # Test health endpoint
        print("2. Testing health endpoint...")
        health_response = requests.get('http://localhost:8001/_stcore/health', timeout=10)
        print(f"   Health: {health_response.text}")
        
        # Check if the page contains our app content
        print("3. Checking page content...")
        page_content = response.text.lower()
        
        indicators = [
            ('streamlit', 'Streamlit framework'),
            ('openai forward', 'OpenAI Forward title'),
            ('forward configuration', 'Configuration section'),
            ('api key', 'API key management'),
            ('rate limit', 'Rate limiting'),
            ('cache', 'Cache settings')
        ]
        
        found_indicators = []
        for indicator, description in indicators:
            if indicator in page_content:
                found_indicators.append((indicator, description))
                print(f"   ✅ Found: {description}")
            else:
                print(f"   ❌ Missing: {description}")
        
        # Test if we can access the app's API endpoints
        print("4. Testing Streamlit API endpoints...")
        try:
            config_response = requests.get('http://localhost:8001/_stcore/app-config', timeout=5)
            print(f"   App config: {config_response.status_code}")
        except Exception as e:
            print(f"   App config error: {str(e)}")
        
        # Summary
        print("\n📊 Summary:")
        print(f"   Found {len(found_indicators)}/{len(indicators)} content indicators")
        
        if len(found_indicators) >= 3:
            print("   ✅ WebUI appears to be working correctly")
            return True
        else:
            print("   ⚠️ WebUI may not be displaying correct content")
            print("   📝 Page title:", response.text.split('<title>')[1].split('</title>')[0] if '<title>' in response.text else 'Not found')
            return False
            
    except Exception as e:
        print(f"❌ Error testing WebUI: {str(e)}")
        return False

def test_api_integration():
    """Test the API integration."""
    print("\n🔗 Testing API Integration:")
    try:
        api_response = requests.get('http://localhost:8000/healthz', timeout=5)
        if api_response.status_code == 200:
            print("   ✅ API server is responding")
            return True
        else:
            print(f"   ❌ API server error: {api_response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API server not accessible: {str(e)}")
        return False

def provide_solutions():
    """Provide solutions if WebUI is not working correctly."""
    print("\n🔧 Troubleshooting Solutions:")
    print("1. Try refreshing your browser page")
    print("2. Clear browser cache and reload")
    print("3. Check if JavaScript is enabled in your browser")
    print("4. Try accessing: http://localhost:8001 in an incognito/private window")
    print("5. Restart the WebUI service:")
    print("   pkill -f streamlit")
    print("   PYTHONPATH=/Users/zhiguangsong/arkSong/openai-forward-main streamlit run openai_forward/webui/run.py --server.port 8001 --server.headless true")

if __name__ == "__main__":
    print("🚀 OpenAI Forward WebUI Content Test")
    print("=" * 60)
    
    webui_ok = test_webui_content()
    api_ok = test_api_integration()
    
    print("\n" + "=" * 60)
    if webui_ok and api_ok:
        print("🎉 WebUI Test Result: SUCCESS")
        print("📱 Access WebUI at: http://localhost:8001")
        print("🔧 Access API at: http://localhost:8000")
    else:
        print("⚠️ WebUI Test Result: ISSUES DETECTED")
        provide_solutions() 