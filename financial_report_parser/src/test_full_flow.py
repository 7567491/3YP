import requests
import os
from dotenv import load_dotenv
import json
import time

def test_full_flow():
    load_dotenv()
    api_key = os.getenv("MOONSHOT_API_KEY")
    
    base_url = "https://api.moonshot.cn/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 1. 测试模型列表
    print("\n1. 获取可用模型列表")
    try:
        response = requests.get(
            f"{base_url}/models",
            headers=headers
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"错误: {str(e)}")
    
    time.sleep(1)  # 添加延迟避免请求过快
    
    # 2. 测试简单对话
    print("\n2. 测试简单对话")
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": "moonshot-v1-8k",
                "messages": [
                    {"role": "system", "content": "你是一个助手。"},
                    {"role": "user", "content": "你好"}
                ],
                "temperature": 0.1
            }
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    test_full_flow() 