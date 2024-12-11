import requests
import os
from dotenv import load_dotenv

def test_moonshot():
    load_dotenv()
    api_key = os.getenv("KIMI_API_KEY")
    api_base = os.getenv("KIMI_API_BASE")
    default_model = os.getenv("KIMI_DEFAULT_MODEL")
    
    # Moonshot API 配置
    url = api_base
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 测试用例
    test_cases = [
        {
            "name": "基础对话",
            "data": {
                "model": default_model,
                "messages": [{"role": "user", "content": "你好"}]
            }
        },
        {
            "name": "带系统提示的对话",
            "data": {
                "model": default_model,
                "messages": [
                    {"role": "system", "content": "你是一个AI助手"},
                    {"role": "user", "content": "你好"}
                ]
            }
        },
        {
            "name": "带参数的对话",
            "data": {
                "model": default_model,
                "messages": [{"role": "user", "content": "你好"}],
                "temperature": 0.7,
                "top_p": 1,
                "max_tokens": 100
            }
        }
    ]
    
    for test in test_cases:
        print(f"\n测试: {test['name']}")
        try:
            response = requests.post(url, headers=headers, json=test['data'])
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            print(f"响应: {response.text}")
        except Exception as e:
            print(f"错误: {str(e)}")

if __name__ == "__main__":
    test_moonshot() 