from pathlib import Path
import os
from dotenv import load_dotenv, find_dotenv

def check_env():
    # 查找.env文件
    env_path = find_dotenv()
    print(f"找到.env文件: {env_path}")
    
    # 读取文件内容
    if env_path:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print("\n.env文件内容:")
            print("-" * 50)
            print(content)
            print("-" * 50)
    
    # 加载环境变量
    load_dotenv()
    
    # 检查环境变量
    api_key = os.getenv("MOONSHOT_API_KEY")
    if api_key:
        print(f"\nAPI密钥已加载: {api_key[:5]}...")
        print(f"API密钥长度: {len(api_key)}")
        print(f"是否以'sk-'开头: {api_key.startswith('sk-')}")
    else:
        print("\n未找到API密钥!")

if __name__ == "__main__":
    check_env() 