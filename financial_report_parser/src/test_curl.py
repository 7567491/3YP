import os
import subprocess
from dotenv import load_dotenv

def test_curl():
    load_dotenv()
    api_key = os.getenv("MOONSHOT_API_KEY")
    
    curl_command = f'''
    curl -X POST "https://api.moonshot.cn/v1/chat/completions" \\
         -H "Content-Type: application/json" \\
         -H "Authorization: Bearer {api_key}" \\
         -d '{{"model": "moonshot-v1-8k", "messages": [{{"role": "user", "content": "你好"}}], "temperature": 0.1}}'
    '''
    
    print("执行curl命令:")
    print(curl_command.replace(api_key, f"{api_key[:5]}..."))
    
    try:
        result = subprocess.run(
            curl_command,
            shell=True,
            capture_output=True,
            text=True
        )
        print("\n响应:")
        print(f"状态码: {result.returncode}")
        print(f"输出: {result.stdout}")
        if result.stderr:
            print(f"错误: {result.stderr}")
    except Exception as e:
        print(f"执行出错: {str(e)}")

if __name__ == "__main__":
    test_curl() 