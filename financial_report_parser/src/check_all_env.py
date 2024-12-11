import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv, dotenv_values

def check_all_env():
    print("环境变量检查报告")
    print("=" * 50)
    
    # 1. 检查当前环境
    print("\n1. 当前环境信息:")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python路径: {os.sys.path}")
    
    # 2. 查找所有.env文件
    print("\n2. 查找.env文件:")
    possible_locations = [
        Path.cwd(),  # 当前目录
        Path.cwd().parent,  # 父目录
        Path.cwd() / 'financial_report_parser',  # 项目目录
        Path(__file__).parent.parent,  # src的父目录
    ]
    
    env_files = []
    for loc in possible_locations:
        env_file = loc / '.env'
        if env_file.exists():
            env_files.append(env_file)
            print(f"\n发现.env文件: {env_file}")
            try:
                env_content = dotenv_values(env_file)
                if 'MOONSHOT_API_KEY' in env_content:
                    key = env_content['MOONSHOT_API_KEY']
                    print(f"包含API密钥: {key[:5]}...")
                    print(f"密钥长度: {len(key)}")
                else:
                    print("未找到 MOONSHOT_API_KEY")
            except Exception as e:
                print(f"读取失败: {str(e)}")
    
    if not env_files:
        print("未找到任何.env文件!")
    
    # 3. 检查环境变量
    print("\n3. 环境变量检查:")
    api_key = os.getenv("MOONSHOT_API_KEY")
    if api_key:
        print(f"环境变量中的API密钥: {api_key[:5]}...")
        print(f"密钥长度: {len(api_key)}")
    else:
        print("环境变量中未找到 MOONSHOT_API_KEY")
    
    # 4. 尝试直接加载
    print("\n4. 尝试直接加载.env:")
    env_path = find_dotenv()
    if env_path:
        print(f"找到.env文件: {env_path}")
        load_dotenv(env_path)
        api_key = os.getenv("MOONSHOT_API_KEY")
        if api_key:
            print(f"加载后的API密钥: {api_key[:5]}...")
        else:
            print("加载后仍未找到API密钥")
    else:
        print("未找到.env文件")

if __name__ == "__main__":
    check_all_env() 