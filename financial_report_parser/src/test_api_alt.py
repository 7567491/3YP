import requests
from dotenv import load_dotenv
import os

def test_alternative():
    load_dotenv()
    api_key = os.getenv("MOONSHOT_API_KEY")
    
    # 测试不同的认证格式
    auth_formats = [
        f"Bearer {api_key}",
        api_key,
        f"bearer {api_key}",
        f"Bearer sk-{api_key.replace('sk-', '')}"
    ]
    
    for auth in auth_formats:
        print(f"\n测试认证格式: {auth[:10]}...")
        headers = {
            "Authorization": auth,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                "https://api.moonshot.cn/v1/chat/completions",
                headers=headers,
                json={
                    "model": "moonshot-v1-8k",
                    "messages": [{"role": "user", "content": "你好"}],
                    "temperature": 0.1
                }
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
        except Exception as e:
            print(f"错误: {str(e)}")

if __name__ == "__main__":
    test_alternative() 