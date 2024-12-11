import os
import requests
import json
from dotenv import load_dotenv

def test_direct():
    load_dotenv()
    api_key = os.getenv("KIMI_API_KEY")
    api_base = os.getenv("KIMI_API_BASE")
    default_model = os.getenv("KIMI_DEFAULT_MODEL")
    
    # 测试不同的模型
    models = [default_model, "moonshot-v1-32k", "moonshot-v1-128k"]
    
    for model in models:
        print(f"\n测试模型: {model}")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Hello!"}
            ],
            "temperature": 0.7
        }
        
        try:
            response = requests.post(api_base, headers=headers, json=data)
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            print(f"响应: {response.text}")
        except Exception as e:
            print(f"错误: {str(e)}")

if __name__ == "__main__":
    test_direct() 