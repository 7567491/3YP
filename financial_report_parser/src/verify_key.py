import os
import re
from dotenv import load_dotenv, find_dotenv
import base64

def verify_key():
    # 加载环境变量
    env_path = find_dotenv()
    load_dotenv(env_path)
    api_key = os.getenv("MOONSHOT_API_KEY")
    
    print("API密钥验证报告")
    print("-" * 50)
    
    if not api_key:
        print("错误: 未找到API密钥")
        return
    
    # 基本检查
    checks = {
        "长度检查": len(api_key) >= 32,
        "前缀检查": api_key.startswith("sk-"),
        "字符集检查": bool(re.match(r'^sk-[A-Za-z0-9_-]+$', api_key)),
        "Base64检查": is_base64_compatible(api_key[3:])  # 去掉sk-前缀后检查
    }
    
    # 打印检查结果
    for check_name, result in checks.items():
        status = "✓" if result else "✗"
        print(f"{check_name}: {status}")
    
    # 详细信息
    print("\n详细信息:")
    print(f"密钥长度: {len(api_key)}")
    print(f"前缀: {api_key[:3]}")
    print(f"字符分布: {analyze_chars(api_key)}")
    
    # 建议
    if not all(checks.values()):
        print("\n建议:")
        if not checks["长度检查"]:
            print("- API密钥似乎太短，请检查是否完整复制")
        if not checks["前缀检查"]:
            print("- API密钥应该以'sk-'开头")
        if not checks["字符集检查"]:
            print("- API密钥包含非法字符，应只包含字母、数字、下划线和连字符")
        if not checks["Base64检查"]:
            print("- API密钥格式可能不正确，请重新生成")

def is_base64_compatible(s):
    """检查字符串是否符合Base64格式"""
    try:
        # 添加可能缺少的填充
        padding = 4 - (len(s) % 4) if len(s) % 4 else 0
        s = s + "=" * padding
        base64.b64decode(s)
        return True
    except:
        return False

def analyze_chars(key):
    """分析密钥中的字符分布"""
    analysis = {
        "字母": sum(c.isalpha() for c in key),
        "数字": sum(c.isdigit() for c in key),
        "特殊字符": sum(not c.isalnum() for c in key)
    }
    return analysis

if __name__ == "__main__":
    verify_key() 