# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
生成安全密钥脚本
用于生成生产环境所需的所有安全密钥
"""

import secrets
import argparse
import sys
from pathlib import Path


def generate_secure_key(length=32):
    """生成安全密钥"""
    return secrets.token_urlsafe(length)


def generate_production_secrets():
    """生成生产环境所需的所有安全密钥"""
    print("🔐 生成生产环境安全密钥")
    print("=" * 60)
    
    # 定义需要生成的密钥
    secrets_list = [
        ("SECRET_KEY", "应用密钥", 32),
        ("API_SECRET_KEY", "API密钥", 32),
        ("JWT_SECRET", "JWT密钥", 32),
        ("SESSION_SECRET", "会话密钥", 32),
        ("REDIS_PASSWORD", "Redis密码", 24),
    ]
    
    results = {}
    
    # 生成所有密钥
    for key_name, description, length in secrets_list:
        key_value = generate_secure_key(length)
        results[key_name] = key_value
        print(f"{description}:")
        print(f"  {key_name}={key_value}")
        print()
    
    # 管理员密码提示
    print("[建议] 管理员密码提示：")
    print("  请设置强密码：至少12位，包含大小写字母、数字和特殊字符")
    print("  示例：Admin@ClawAI2024!Secure")
    print()
    
    # 生成.env.production更新内容
    env_content = "# 安全密钥 - 自动生成（请妥善保管）\n"
    for key_name, key_value in results.items():
        env_content += f"{key_name}={key_value}\n"
    
    # 询问是否要写入文件
    print("=" * 60)
    choice = input("是否要将这些密钥写入 .env.production 文件？ (y/N): ").strip().lower()
    
    if choice == 'y':
        env_file = Path(".env.production")
        
        if env_file.exists():
            # 读取现有文件
            with open(env_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            # 替换现有密钥
            new_lines = []
            for line in existing_content.split('\n'):
                replaced = False
                for key_name in results.keys():
                    if line.strip().startswith(f"{key_name}="):
                        new_lines.append(f"{key_name}={results[key_name]}")
                        replaced = True
                        break
                if not replaced:
                    new_lines.append(line)
            
            new_content = '\n'.join(new_lines)
            
            # 备份原文件
            backup_file = env_file.with_suffix('.backup')
            import shutil
            shutil.copy2(env_file, backup_file)
            print(f"[成功] 原文件已备份到: {backup_file}")
            
            # 写入新文件
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"[成功] 密钥已写入 {env_file}")
            
            # 显示需要手动更新的配置
            print("\n[列表] 需要手动更新的配置项：")
            print("  1. DEEPSEEK_API_KEY - 真实的DeepSeek API密钥")
            print("  2. SMTP_USERNAME - 邮件服务器用户名")
            print("  3. SMTP_PASSWORD - 邮件服务器密码")
            print("  4. REDIS_PASSWORD - 如果Redis需要密码")
            print("  5. 所有工具路径 - 根据实际安装位置调整")
        else:
            print(f"[失败] 文件 {env_file} 不存在，请先创建生产环境配置文件")
            return False
    
    # 生成独立的密钥文件
    secrets_file = Path("production_secrets.txt")
    with open(secrets_file, 'w', encoding='utf-8') as f:
        f.write("# ClawAI 生产环境安全密钥\n")
        f.write("# 生成时间: " + secrets_file.stat().st_ctime + "\n")
        f.write("# 重要：请妥善保管此文件，不要提交到代码仓库\n\n")
        for key_name, key_value in results.items():
            f.write(f"{key_name}={key_value}\n")
        f.write("\n# 安全提示：\n")
        f.write("# 1. 定期轮换这些密钥\n")
        f.write("# 2. 使用密钥管理工具存储\n")
        f.write("# 3. 限制密钥的访问权限\n")
        f.write("# 4. 监控密钥的使用情况\n")
    
    print(f"[成功] 密钥已保存到独立文件: {secrets_file}")
    print("[警告]  警告：请勿将此文件提交到代码仓库或分享给未授权人员")
    
    return True


def generate_docker_secrets():
    """生成Docker环境使用的密钥文件"""
    print("\n🐳 生成Docker secrets文件")
    print("-" * 40)
    
    docker_secrets_dir = Path("docker/secrets")
    docker_secrets_dir.mkdir(parents=True, exist_ok=True)
    
    docker_secrets = {
        "secret_key": generate_secure_key(32),
        "jwt_secret": generate_secure_key(32),
        "api_secret": generate_secure_key(32),
        "session_secret": generate_secure_key(32),
        "redis_password": generate_secure_key(24),
        "db_password": generate_secure_key(24),
    }
    
    for secret_name, secret_value in docker_secrets.items():
        secret_file = docker_secrets_dir / secret_name
        with open(secret_file, 'w', encoding='utf-8') as f:
            f.write(secret_value)
        print(f"  {secret_name}: {secret_file}")
    
    # 生成docker-compose环境变量文件
    compose_env_file = Path("docker/.env.docker")
    with open(compose_env_file, 'w', encoding='utf-8') as f:
        f.write("# Docker Compose 环境变量\n")
        f.write("# 自动生成 - 请勿手动编辑\n\n")
        f.write(f"SECRET_KEY={docker_secrets['secret_key']}\n")
        f.write(f"JWT_SECRET={docker_secrets['jwt_secret']}\n")
        f.write(f"API_SECRET_KEY={docker_secrets['api_secret']}\n")
        f.write(f"SESSION_SECRET={docker_secrets['session_secret']}\n")
        f.write(f"REDIS_PASSWORD={docker_secrets['redis_password']}\n")
        f.write(f"POSTGRES_PASSWORD={docker_secrets['db_password']}\n")
        f.write("\n# 其他配置\n")
        f.write("POSTGRES_USER=clawai\n")
        f.write("POSTGRES_DB=clawai_production\n")
        f.write("POSTGRES_HOST=postgres\n")
        f.write("POSTGRES_PORT=5432\n")
    
    print(f"[成功] Docker环境变量文件: {compose_env_file}")
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成ClawAI生产环境安全密钥')
    parser.add_argument('--docker', action='store_true', help='生成Docker secrets')
    parser.add_argument('--all', action='store_true', help='生成所有密钥')
    parser.add_argument('--output', type=str, help='输出文件路径')
    
    args = parser.parse_args()
    
    try:
        print("🔐 ClawAI 安全密钥生成工具")
        print("=" * 60)
        
        success = True
        
        if args.docker or args.all:
            success = generate_docker_secrets() and success
        
        if not args.docker or args.all:
            success = generate_production_secrets() and success
        
        if args.output:
            # 将密钥写入指定文件
            import json
            secrets_data = {
                "secret_key": generate_secure_key(32),
                "jwt_secret": generate_secure_key(32),
                "api_secret": generate_secure_key(32),
            }
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(secrets_data, f, indent=2)
            
            print(f"[成功] 密钥已写入: {args.output}")
        
        if success:
            print("\n[庆祝] 密钥生成完成！")
            print("\n[列表] 下一步：")
            print("  1. 更新 .env.production 中的其他配置项")
            print("  2. 配置真实的API密钥和邮件服务器")
            print("  3. 确保所有工具路径正确")
            print("  4. 测试生产环境配置")
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"[失败] 生成密钥时出错: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())