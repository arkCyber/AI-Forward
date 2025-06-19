#!/usr/bin/env python3
"""Quick test for Ollama functionality"""

import asyncio
import httpx

async def test_ollama():
    client = httpx.AsyncClient(timeout=30.0)
    headers = {
        'Authorization': 'Bearer sk-8d6804b011614dba7bd065f8644514b',
        'Content-Type': 'application/json'
    }
    
    # 测试不同模型
    models = ['llama3.2', 'qwen2:1.5b', 'qwen2:7b']
    
    print("🧪 Testing Ollama models...")
    print("=" * 50)
    
    for model in models:
        try:
            response = await client.post(
                'http://localhost:9000/v1/chat/completions',
                headers=headers,
                json={
                    'model': model,
                    'messages': [{'role': 'user', 'content': f'Hello from {model}! Say hi back briefly.'}],
                    'max_tokens': 30
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                router_info = data.get('_router_info', {})
                provider = router_info.get('provider', 'unknown')
                response_time = router_info.get('response_time', 0)
                
                print(f'✅ {model}: "{content[:60]}..." (via {provider}, {response_time:.2f}s)')
            else:
                print(f'❌ {model}: HTTP {response.status_code} - {response.text[:100]}')
                
        except Exception as e:
            print(f'❌ {model}: Exception - {str(e)[:100]}')
    
    # Test health and stats
    print("\n📊 Service Status:")
    print("-" * 30)
    
    try:
        health_response = await client.get('http://localhost:9000/health')
        if health_response.status_code == 200:
            health_data = health_response.json()
            status = health_data.get('status', 'unknown')
            print(f'Health: {status}')
            
            providers = health_data.get('providers', {})
            for name, info in providers.items():
                provider_status = info.get('status', 'unknown')
                response_time = info.get('response_time', 0)
                print(f'  {name}: {provider_status} ({response_time:.2f}s)')
        else:
            print(f'Health check failed: HTTP {health_response.status_code}')
    except Exception as e:
        print(f'Health check error: {str(e)}')
    
    await client.aclose()
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_ollama()) 