import os
from pathlib import Path
from dotenv import find_dotenv, load_dotenv

def check_env_path():
    # 检查当前工作目录
    print(f"当前工作目录: {os.getcwd()}")
    
    # 查找.env文件
    env_path = find_dotenv()
    print(f"\n找到的.env文件路径: {env_path}")
    
    # 检查项目根目录下是否有.env文件
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'
    print(f"项目根目录下的.env文件路径: {env_file}")
    print(f"该文件是否存在: {env_file.exists()}")
    
    # 加载环境变量并检查
    load_dotenv(env_path)
    api_key = os.getenv("MOONSHOT_API_KEY")
    
    if api_key:
        print(f"\nAPI密钥已加载:")
        print(f"长度: {len(api_key)}")
        print(f"前缀: {api_key[:5]}...")
        print(f"是否包含空格: {'是' if ' ' in api_key else '否'}")
        print(f"是否包含换行符: {'是' if '\n' in api_key else '否'}")
    else:
        print("\n未能加载API密钥!")
    
    # 列出所有相关环境变量
    print("\n所有包含 'MOONSHOT' 的环境变量:")
    for key, value in os.environ.items():
        if 'MOONSHOT' in key:
            print(f"{key}: {value[:5]}...")

if __name__ == "__main__":
    check_env_path() 