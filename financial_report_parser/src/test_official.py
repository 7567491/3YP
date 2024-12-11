import requests
import os
from dotenv import load_dotenv
import json

def test_official():
    load_dotenv()
    api_key = os.getenv("MOONSHOT_API_KEY")
    
    url = "https://api.moonshot.cn/v1/chat/completions"
    
    # 官方示例格式
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "moonshot-v1-8k",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Hello!"
            }
        ],
        "temperature": 0.7
    }
    
    print("发送请求...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print("\n响应信息:")
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 401:
            print("\n可能的问题:")
            print("1. API密钥可能已过期")
            print("2. API密钥可能被禁用")
            print("3. API密钥格式可能不正确")
            print("4. 账户可能有访问限制")
            
    except Exception as e:
        print(f"请求失败: {str(e)}")

if __name__ == "__main__":
    test_official() 