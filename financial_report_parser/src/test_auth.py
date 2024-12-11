import requests
import os
from dotenv import load_dotenv
import json

def test_auth():
    load_dotenv()
    api_key = os.getenv("MOONSHOT_API_KEY")
    
    # 测试不同的认证头格式
    auth_headers = [
        # 标准格式
        {"Authorization": f"Bearer {api_key}"},
        # 不带Bearer
        {"Authorization": api_key},
        # 小写bearer
        {"Authorization": f"bearer {api_key}"},
        # 直接使用sk-前缀
        {"Authorization": f"Bearer {api_key if api_key.startswith('sk-') else f'sk-{api_key}'}"},
        # 移除可能的空格
        {"Authorization": f"Bearer{api_key.strip()}"},
        # API密钥作为查询参数
        {}  # 将在URL中添加api_key参数
    ]
    
    base_url = "https://api.moonshot.cn/v1"
    
    for i, headers in enumerate(auth_headers, 1):
        print(f"\n测试认证方式 {i}:")
        print(f"使用头部: {headers}")
        
        try:
            # 添加通用头部
            headers.update({"Content-Type": "application/json"})
            
            # 构造URL（对于最后一种测试方式，添加api_key作为查询参数）
            url = f"{base_url}/chat/completions"
            if not headers.get("Authorization"):
                url += f"?api_key={api_key}"
            
            print(f"请求URL: {url.replace(api_key, 'sk-***')}")
            
            response = requests.post(
                url,
                headers=headers,
                json={
                    "model": "moonshot-v1-8k",
                    "messages": [{"role": "user", "content": "测试"}],
                    "temperature": 0.1
                }
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            print(f"响应内容: {response.text}")
            
        except Exception as e:
            print(f"请求失败: {str(e)}")

if __name__ == "__main__":
    test_auth() 