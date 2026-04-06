# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
统一工具执行器 - 最终版适配器
导入 unified_executor_final.py 中的 UnifiedExecutor 类，并重命名为 UnifiedToolExecutor 以保持向后兼容
"""

import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    # 从 unified_executor_final.py 导入 UnifiedExecutor 类
    from backend.tools.unified_executor_final import UnifiedExecutor
    
    # 将 UnifiedExecutor 重命名为 UnifiedToolExecutor 以保持向后兼容
    UnifiedToolExecutor = UnifiedExecutor
    
    # 重新导出类
    __all__ = ['UnifiedToolExecutor']
    
    print("[OK] 统一工具执行器已成功导入 unified_executor_final.UnifiedExecutor")
    
except ImportError as e:
    # 如果导入失败，创建一个简单的兼容类（回退方案）
    print(f"❌ 无法从 unified_executor_final 导入: {e}")
    print("⚠️  使用兼容模式执行器，功能受限")
    
    # 创建最小兼容类
    class UnifiedToolExecutor:
        """统一工具执行器兼容类（回退模式）"""
        
        def __init__(self, **kwargs):
            """初始化兼容执行器"""
            self.name = "UnifiedToolExecutor (兼容回退模式)"
            self.description = "兼容执行器，功能受限（unified_executor_final 导入失败）"
            self.logger = self._create_logger()
            
        def _create_logger(self):
            """创建日志记录器"""
            import logging
            logger = logging.getLogger(__name__)
            if not logger.handlers:
                handler = logging.StreamHandler(sys.stdout)
                formatter = logging.Formatter('%(levelname)s: %(message)s')
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                logger.setLevel(logging.WARNING)
            return logger
        
        def get_available_tools(self):
            """获取可用工具信息"""
            self.logger.warning("使用兼容回退模式，工具信息受限")
            return {
                "total_tools": 0,
                "installed_tools": 0,
                "installation_rate": 0,
                "tools": {},
                "recommendations": []
            }
        
        def execute_comprehensive_scan(self, target, tools=None):
            """执行综合安全扫描"""
            import time
            self.logger.warning(f"使用兼容回退模式执行扫描，目标: {target}")
            
            # 返回模拟结果
            start_time = time.time()
            end_time = start_time + 2.0
            
            return {
                "target": target,
                "execution_time": 2.0,
                "performance_metrics": {
                    "total_tools": len(tools) if tools else 0,
                    "successful_tools": 0,
                    "failed_tools": len(tools) if tools else 0,
                    "total_execution_time": 2.0,
                    "average_tool_time": 0,
                    "concurrent_executions": 0,
                    "max_concurrent": 0,
                    "tool_times": {},
                    "throughput": 0,
                    "real_execution_ratio": 0
                },
                "results": {},
                "analysis": {
                    "open_ports": 0,
                    "web_technologies": [],
                    "vulnerabilities": [],
                    "attack_surface": [],
                    "risk_level": "unknown",
                    "services_detected": [],
                    "execution_stats": {
                        "total_tools": 0,
                        "real_executions": 0,
                        "simulated_executions": 0,
                        "failed_executions": 0
                    }
                },
                "summary": "兼容回退模式扫描完成，无实际工具执行",
                "config": {
                    "execution_strategy": "compatibility",
                    "max_workers": 0,
                    "enable_retry": False,
                    "enable_security": False,
                    "require_real_execution": False
                },
                "tool_installation_report": {
                    "total_tools": 0,
                    "installed_tools": 0,
                    "installation_rate": 0,
                    "tools": {},
                    "recommendations": []
                }
            }
        
        def check_system_health(self):
            """检查系统健康状态"""
            return {
                "overall": {
                    "score": 0.3,
                    "status": "degraded",
                    "details": {
                        "note": "兼容回退模式，功能受限"
                    }
                },
                "tools": self.get_available_tools()
            }


# 测试函数
def test_module():
    """测试模块功能"""
    print("=" * 80)
    print("统一工具执行器模块测试")
    print("=" * 80)
    
    try:
        # 创建执行器实例
        executor = UnifiedToolExecutor()
        
        # 测试基本功能
        print(f"执行器名称: {executor.name}")
        print(f"执行器描述: {executor.description}")
        
        # 测试可用工具信息
        tools_info = executor.get_available_tools()
        print(f"工具状态: {tools_info.get('total_tools', 0)}个工具，安装率: {tools_info.get('installation_rate', 0):.1f}%")
        
        # 测试健康检查
        health = executor.check_system_health()
        print(f"系统健康状态: {health.get('overall', {}).get('status', 'unknown')}")
        
        print("\n✅ 模块测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 模块测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行测试
    success = test_module()
    
    if success:
        print("\n" + "=" * 80)
        print("统一工具执行器模块已准备好")
        print("=" * 80)
        print("\n用法示例:")
        print("from backend.tools.unified_executor import UnifiedToolExecutor")
        print("executor = UnifiedToolExecutor()")
        print("result = executor.execute_comprehensive_scan('example.com')")
    else:
        print("\n❌ 模块测试失败，请检查配置")