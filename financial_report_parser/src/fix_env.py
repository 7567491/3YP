def fix_env():
    """修复.env文件格式"""
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # 确保密钥格式正确
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    fixed_content = '\n'.join(lines)
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(fixed_content)
        if not fixed_content.endswith('\n'):
            f.write('\n')

if __name__ == '__main__':
    fix_env() 