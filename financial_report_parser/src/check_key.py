import os
from dotenv import load_dotenv, find_dotenv

def check_key():
    env_path = find_dotenv()
    load_dotenv(env_path)
    
    api_key = os.getenv("MOONSHOT_API_KEY")
    
    print("API密钥检查:")
    print("-" * 50)
    print(f"1. 密钥长度: {len(api_key)}")
    print(f"2. 前缀检查: {api_key[:3]}")
    print(f"3. 格式检查: {'仅包含字母和数字' if api_key.replace('-','').isalnum() else '包含特殊字符'}")
    print(f"4. 空白字符检查: {'不含空白字符' if api_key.strip() == api_key else '含有空白字符'}")
    
    # 检查是否有隐藏字符
    hex_chars = ' '.join(hex(ord(c)) for c in api_key)
    print(f"5. 字符编码: {hex_chars}")

if __name__ == "__main__":
    check_key() 