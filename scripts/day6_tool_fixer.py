#!/usr/bin/env python3
"""
Day 6: 工具执行紧急修复脚本
修复核心工具执行问题，提升工具可用性
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

class ToolFixer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.tools_dir = self.project_root / "工具"
        self.external_tools_dir = self.project_root / "external_tools"
        
    def check_tool(self, tool_name, test_cmd):
        """检查工具是否可用"""
        print(f"检查 {tool_name}...")
        try:
            result = subprocess.run(
                test_cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                print(f"  ✅ {tool_name}: 可用")
                print(f"      输出: {result.stdout.strip()[:100]}")
                return True, result.stdout.strip()
            else:
                print(f"  ❌ {tool_name}: 执行失败 (返回码: {result.returncode})")
                print(f"      错误: {result.stderr.strip()[:200]}")
                return False, result.stderr.strip()
        except subprocess.TimeoutExpired:
            print(f"  ⏱️ {tool_name}: 执行超时")
            return False, "执行超时"
        except Exception as e:
            print(f"  ⚠️ {tool_name}: 异常 - {str(e)}")
            return False, str(e)
    
    def fix_nmap(self):
        """修复Nmap问题"""
        print("\n🔧 修复Nmap...")
        
        # 检查是否已安装但不在PATH中
        nmap_paths = [
            "C:\\Program Files (x86)\\Nmap\\nmap.exe",
            "C:\\Program Files\\Nmap\\nmap.exe",
            "C:\\Nmap\\nmap.exe",
        ]
        
        for path in nmap_paths:
            if os.path.exists(path):
                print(f"  找到Nmap: {path}")
                # 创建符号链接或添加到PATH的批处理文件
                return self._create_nmap_wrapper(path)
        
        print("  ⚠️ Nmap未安装")
        print("  安装指南:")
        print("  1. 下载Nmap Windows安装包: https://nmap.org/download.html")
        print("  2. 安装时选择 'Add Nmap to PATH'")
        print("  3. 重启终端后验证: nmap --version")
        return False
    
    def _create_nmap_wrapper(self, nmap_path):
        """创建Nmap包装器"""
        wrapper_path = self.project_root / "tools" / "nmap_wrapper.bat"
        wrapper_content = f'@echo off\n"{nmap_path}" %*\n'
        
        try:
            os.makedirs(self.project_root / "tools", exist_ok=True)
            with open(wrapper_path, "w") as f:
                f.write(wrapper_content)
            
            # 创建Python包装器
            py_wrapper = self.project_root / "tools" / "nmap_wrapper.py"
            py_content = f'''#!/usr/bin/env python3
import subprocess
import sys

def main():
    """Nmap包装器"""
    cmd = ['{nmap_path}'] + sys.argv[1:]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
'''
            with open(py_wrapper, "w") as f:
                f.write(py_content)
            
            print(f"  ✅ 创建Nmap包装器: {wrapper_path}")
            return True
        except Exception as e:
            print(f"  ❌ 创建包装器失败: {str(e)}")
            return False
    
    def fix_wafw00f(self):
        """修复WAFW00F问题"""
        print("\n🔧 修复WAFW00F...")
        
        wafw00f_dir = self.tools_dir / "wafw00f"
        if not wafw00f_dir.exists():
            print(f"  ❌ WAFW00F目录不存在: {wafw00f_dir}")
            return False
        
        # 尝试安装为Python包
        try:
            print("  尝试安装WAFW00F...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "wafw00f"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("  ✅ WAFW00F安装成功")
                return True
            else:
                print(f"  ❌ pip安装失败: {result.stderr[:200]}")
        except Exception as e:
            print(f"  ⚠️ pip安装异常: {str(e)}")
        
        # 尝试从本地目录安装
        try:
            print("  尝试从本地目录安装...")
            setup_py = wafw00f_dir / "setup.py"
            if setup_py.exists():
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-e", str(wafw00f_dir)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("  ✅ 本地安装成功")
                    return True
        except Exception as e:
            print(f"  ⚠️ 本地安装异常: {str(e)}")
        
        # 创建包装器
        return self._create_wafw00f_wrapper()
    
    def _create_wafw00f_wrapper(self):
        """创建WAFW00F包装器"""
        wafw00f_main = self.tools_dir / "wafw00f" / "wafw00f" / "main.py"
        if not wafw00f_main.exists():
            print(f"  ❌ WAFW00F主文件不存在: {wafw00f_main}")
            return False
        
        wrapper_path = self.project_root / "tools" / "wafw00f_wrapper.py"
        wrapper_content = f'''#!/usr/bin/env python3
import sys
import os

# 添加WAFW00F到Python路径
wafw00f_dir = r"{self.tools_dir / "wafw00f"}"
sys.path.insert(0, str(wafw00f_dir))

try:
    from wafw00f import main as wafw00f_main
    wafw00f_main()
except ImportError as e:
    print(f"导入WAFW00F失败: {{e}}")
    print("请尝试: pip install wafw00f")
    sys.exit(1)
'''
        
        try:
            os.makedirs(self.project_root / "tools", exist_ok=True)
            with open(wrapper_path, "w") as f:
                f.write(wrapper_content)
            print(f"  ✅ 创建WAFW00F包装器: {wrapper_path}")
            return True
        except Exception as e:
            print(f"  ❌ 创建包装器失败: {str(e)}")
            return False
    
    def fix_tool_paths(self):
        """修复工具路径配置"""
        print("\n🔧 修复工具路径配置...")
        
        # 更新unified_executor_final.py中的路径
        config_file = self.project_root / "backend" / "tools" / "unified_executor_final.py"
        if not config_file.exists():
            print(f"  ❌ 配置文件不存在: {config_file}")
            return False
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 修改get_tool_path函数，添加Windows路径检查
            new_get_tool_path = '''
        def get_tool_path(config_name: str, default_cmd: str) -> str:
            """获取工具路径，优先级：工具包装器 > PATH > 配置文件路径 > 默认命令"""
            tool_name = default_cmd.lower()
            
            # 1. 使用工具包装器查找（优先）
            if tool_wrapper:
                tool_path = tool_wrapper.find_tool(tool_name)
                if tool_path:
                    self.logger.info(f"工具包装器找到工具 {tool_name}: {tool_path}")
                    return str(tool_path)
            
            # 2. 检查PATH
            tool_path = shutil.which(tool_name)
            if tool_path:
                self.logger.info(f"PATH中找到工具 {tool_name}: {tool_path}")
                return tool_path
            
            # 3. 检查项目工具目录
            project_tools_dir = os.path.join(os.path.dirname(__file__), '..', '..', '工具')
            if os.path.exists(project_tools_dir):
                # 查找可执行文件
                tool_path = self._find_executable_in_dir(
                    os.path.join(project_tools_dir, tool_name)
                )
                if tool_path:
                    self.logger.info(f"项目工具目录找到工具 {tool_name}: {tool_path}")
                    return tool_path
            
            # 4. 检查外部工具目录
            external_tools_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'external_tools')
            if os.path.exists(external_tools_dir):
                tool_path = self._find_executable_in_dir(
                    os.path.join(external_tools_dir, tool_name)
                )
                if tool_path:
                    self.logger.info(f"外部工具目录找到工具 {tool_name}: {tool_path}")
                    return tool_path
            
            # 5. Windows特定路径检查
            if sys.platform == "win32":
                windows_paths = {
                    "nmap": [
                        "C:\\\\Program Files (x86)\\\\Nmap\\\\nmap.exe",
                        "C:\\\\Program Files\\\\Nmap\\\\nmap.exe",
                        "C:\\\\Nmap\\\\nmap.exe",
                    ],
                    "nuclei": [
                        "C:\\\\Tools\\\\nuclei\\\\nuclei.exe",
                        "C:\\\\Program Files\\\\nuclei\\\\nuclei.exe",
                    ],
                    "whatweb": [
                        "C:\\\\Tools\\\\WhatWeb\\\\whatweb",
                        "C:\\\\Program Files\\\\WhatWeb\\\\whatweb.exe",
                    ],
                }
                if tool_name in windows_paths:
                    for path in windows_paths[tool_name]:
                        if os.path.exists(path):
                            self.logger.info(f"Windows路径找到工具 {tool_name}: {path}")
                            return path
            
            # 6. 返回默认命令
            self.logger.warning(f"工具 {tool_name} 未找到，使用默认命令: {default_cmd}")
            return default_cmd
'''
            
            # 替换get_tool_path函数
            import re
            pattern = r'def get_tool_path\(config_name: str, default_cmd: str\) -> str:.*?return default_cmd'
            content = re.sub(pattern, new_get_tool_path, content, flags=re.DOTALL)
            
            with open(config_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            print("  ✅ 更新工具路径配置")
            return True
        except Exception as e:
            print(f"  ❌ 更新配置失败: {str(e)}")
            return False
    
    def create_tool_verifier(self):
        """创建工具验证脚本"""
        print("\n📋 创建工具验证脚本...")
        
        verifier_path = self.project_root / "verify_tools.py"
        verifier_content = '''#!/usr/bin/env python3
"""
工具验证脚本
检查所有核心工具是否可用
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def test_tool(tool_name, cmd):
    """测试单个工具"""
    print(f'测试 {tool_name}...')
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f'  [OK] {tool_name}: 可用')
            print(f'      输出: {result.stdout.strip()[:100]}')
            return True, result.stdout.strip()
        else:
            print(f'  [FAIL] {tool_name}: 执行失败 (返回码: {result.returncode})')
            print(f'      错误: {result.stderr.strip()[:200]}')
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        print(f'  [TIMEOUT] {tool_name}: 执行超时')
        return False, "执行超时"
    except Exception as e:
        print(f'  [ERROR] {tool_name}: 异常 - {str(e)}')
        return False, str(e)

def main():
    """主函数"""
    print("核心工具执行状态测试")
    print("=" * 60)
    
    # 测试工具列表
    tools = [
        ("nmap", "nmap --version"),
        ("python", "python --version"),
        ("sqlmap", "python -m sqlmap --version"),
        ("nuclei", "nuclei --version"),
        ("whatweb", "whatweb --version"),
        ("dirsearch", "python -m dirsearch --version"),
        ("wafw00f", "python -m wafw00f --version"),
    ]
    
    results = {}
    success_count = 0
    
    for tool_name, cmd in tools:
        success, output = test_tool(tool_name, cmd)
        results[tool_name] = {
            "success": success,
            "command": cmd,
            "output": output
        }
        if success:
            success_count += 1
    
    print("=" * 60)
    print(f"测试完成: {success_count}/{len(tools)} 个工具可用")
    
    # 保存结果
    with open("tool_verification_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 提供建议
    if success_count < len(tools):
        print("\n[WARNING] 核心工具可用性不足，需要修复")
        print("建议修复步骤:")
        for tool_name, data in results.items():
            if not data["success"]:
                print(f"1. {tool_name}: {data['output'][:100]}")
    
    return success_count == len(tools)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''
        
        try:
            with open(verifier_path, "w") as f:
                f.write(verifier_content)
            print(f"  ✅ 创建工具验证脚本: {verifier_path}")
            return True
        except Exception as e:
            print(f"  ❌ 创建验证脚本失败: {str(e)}")
            return False
    
    def run(self):
        """运行修复程序"""
        print("=" * 60)
        print("Day 6: 工具执行紧急修复")
        print("=" * 60)
        
        # 1. 检查当前状态
        print("\n📊 当前工具状态:")
        tools_to_check = [
            ("nmap", "nmap --version"),
            ("python", "python --version"),
            ("sqlmap", "python -m sqlmap --version"),
            ("nuclei", "nuclei --version"),
            ("whatweb", "whatweb --version"),
            ("dirsearch", "python -m dirsearch --version"),
            ("wafw00f", "python -m wafw00f --version"),
        ]
        
        initial_results = {}
        for tool_name, cmd in tools_to_check:
            success, output = self.check_tool(tool_name, cmd)
            initial_results[tool_name] = success
        
        initial_success = sum(initial_results.values())
        print(f"\n初始状态: {initial_success}/{len(tools_to_check)} 个工具可用")
        
        # 2. 执行修复
        print("\n🛠️ 开始修复...")
        
        fixes = [
            ("修复工具路径配置", self.fix_tool_paths),
            ("修复WAFW00F", self.fix_wafw00f),
            ("修复Nmap", self.fix_nmap),
            ("创建工具验证脚本", self.create_tool_verifier),
        ]
        
        for fix_name, fix_func in fixes:
            print(f"\n{fix_name}...")
            try:
                fix_func()
            except Exception as e:
                print(f"  ⚠️ 修复失败: {str(e)}")
        
        # 3. 验证修复结果
        print("\n✅ 修复完成")
        print("\n📋 验证修复结果:")
        
        print("\n运行工具验证脚本...")
        verifier_path = self.project_root / "verify_tools.py"
        if verifier_path.exists():
            result = subprocess.run(
                [sys.executable, str(verifier_path)],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.stderr:
                print("错误:", result.stderr[:500])
        
        print("\n🎯 Day 6工具修复完成")
        print("下一步:")
        print("1. 运行: python verify_tools.py")
        print("2. 运行: python test_tool_execution.py")
        print("3. 运行: python test_dvwa_integration.py")

if __name__ == "__main__":
    fixer = ToolFixer()
    fixer.run()
