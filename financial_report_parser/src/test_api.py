import requests
import os
from dotenv import load_dotenv, find_dotenv

def test_api():
    # 检查环境变量加载
    env_path = find_dotenv()
    print(f"加载环境变量文件: {env_path}")
    load_dotenv(env_path)
    
    api_key = os.getenv("MOONSHOT_API_KEY")
    print(f"\nAPI密钥信息:")
    print(f"密钥前缀: {api_key[:5] if api_key else 'None'}")
    print(f"密钥长度: {len(api_key) if api_key else 0}")
    
    # 构造请求
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print("\n请求信息:")
    print(f"Authorization头: Bearer {api_key[:5]}...")
    print("Content-Type:", headers["Content-Type"])
    
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
        
        print(f"\n响应信息:")
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n请求异常: {str(e)}")

if __name__ == "__main__":
    test_api() 