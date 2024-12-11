import requests
import os
from dotenv import load_dotenv

def test_endpoint():
    load_dotenv()
    api_key = os.getenv("MOONSHOT_API_KEY")
    
    endpoints = [
        "https://api.moonshot.cn/v1",
        "https://api.moonshot.cn/v1/models",  # 测试模型列表接口
        "https://api.moonshot.cn/v1/chat/completions"  # 测试聊天接口
    ]
    
    for endpoint in endpoints:
        print(f"\n测试端点: {endpoint}")
        try:
            # 对于 chat/completions 使用 POST，其他使用 GET
            if 'chat/completions' in endpoint:
                response = requests.post(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "moonshot-v1-8k",
                        "messages": [{"role": "user", "content": "测试"}],
                        "temperature": 0.1
                    }
                )
            else:
                response = requests.get(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                )
            
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            print(f"响应内容: {response.text}")
            
        except Exception as e:
            print(f"请求失败: {str(e)}")

if __name__ == "__main__":
    test_endpoint() 