#!/usr/bin/env python3
"""
ClawAI 工具配置验证脚本
验证所有YAML工具配置文件的语法和结构
"""

import os
import sys
import yaml
import json
from pathlib import Path

def validate_yaml_file(filepath):
    """验证单个YAML文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            data = yaml.safe_load(content)
        
        # 基本验证
        required_fields = ['name', 'command', 'category', 'description']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return False, f"缺少必需字段: {', '.join(missing_fields)}"
        
        # 验证工具名称与文件名一致
        filename = os.path.basename(filepath)
        expected_name = filename.replace('.yaml', '')
        if data['name'] != expected_name:
            return False, f"工具名称 '{data['name']}' 与文件名 '{expected_name}' 不匹配"
        
        # 验证参数结构
        if 'parameters' in data:
            for param in data['parameters']:
                if 'name' not in param:
                    return False, "参数缺少 'name' 字段"
                if 'type' not in param:
                    return False, f"参数 '{param.get('name', '未知')}' 缺少 'type' 字段"
        
        return True, "验证通过"
        
    except yaml.YAMLError as e:
        return False, f"YAML语法错误: {str(e)}"
    except Exception as e:
        return False, f"验证错误: {str(e)}"

def validate_tool_loader():
    """验证工具加载器是否能正确加载配置"""
    try:
        # 尝试导入工具加载器
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'tool-executor'))
        from tool_loader import ToolLoader
        
        loader = ToolLoader()
        tools = loader.list_tools()
        
        return True, f"工具加载器正常工作，加载了 {len(tools)} 个工具"
        
    except ImportError as e:
        return False, f"无法导入工具加载器: {str(e)}"
    except Exception as e:
        return False, f"工具加载器错误: {str(e)}"

def main():
    print("=" * 60)
    print("ClawAI 工具配置验证")
    print("=" * 60)
    
    # 1. 查找所有工具配置文件
    config_dir = os.path.join('config', 'tools')
    if not os.path.exists(config_dir):
        print(f"❌ 配置目录不存在: {config_dir}")
        return 1
    
    yaml_files = list(Path(config_dir).glob('*.yaml'))
    print(f"找到 {len(yaml_files)} 个工具配置文件:")
    print()
    
    # 2. 验证每个配置文件
    validation_results = []
    all_valid = True
    
    for yaml_file in sorted(yaml_files):
        print(f"验证: {yaml_file.name}...", end=" ")
        is_valid, message = validate_yaml_file(yaml_file)
        
        if is_valid:
            print("✅ 通过")
            validation_results.append((yaml_file.name, True, message))
        else:
            print("❌ 失败")
            print(f"   错误: {message}")
            validation_results.append((yaml_file.name, False, message))
            all_valid = False
    
    # 3. 验证工具加载器
    print()
    print("验证工具加载器...", end=" ")
    loader_valid, loader_message = validate_tool_loader()
    
    if loader_valid:
        print("✅ 通过")
        print(f"   {loader_message}")
    else:
        print("❌ 失败")
        print(f"   错误: {loader_message}")
        all_valid = False
    
    # 4. 汇总结果
    print()
    print("=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    valid_count = sum(1 for _, is_valid, _ in validation_results if is_valid)
    total_count = len(validation_results)
    
    print(f"配置文件: {valid_count}/{total_count} 通过")
    print(f"工具加载器: {'✅ 通过' if loader_valid else '❌ 失败'}")
    print()
    
    if all_valid:
        print("🎉 所有验证通过！工具配置准备就绪。")
        return 0
    else:
        print("⚠️  存在验证失败，请修复上述问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
