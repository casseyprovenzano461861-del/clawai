#!/usr/bin/env python3
"""
P1阶段导入验证测试
验证所有核心模块可以正常导入
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

print("=" * 60)
print("P1阶段模块导入验证测试")
print("=" * 60)

# 测试导入的模块列表
modules_to_test = [
    # HackSynth AI组件
    ("src.shared.backend.ai.hacksynth.planner", "HackSynthPlanner"),
    ("src.shared.backend.ai.hacksynth.llm_planner", "LLMHackSynthPlanner"),
    ("src.shared.backend.ai.hacksynth.summarizer", "HackSynthSummarizer"),
    ("src.shared.backend.ai.hacksynth.llm_summarizer", "LLMHackSynthSummarizer"),
    ("src.shared.backend.ai.hacksynth.manager", "HackSynthManager"),

    # 安全验证
    ("src.shared.backend.security.input_validation", "SecureInputValidator"),

    # LLM编排器
    ("src.shared.backend.ai_core.llm_orchestrator", "LLMOrchestrator"),

    # 审计系统 (P1-7)
    ("src.shared.backend.audit.manager", "AuditManager"),

    # 监控指标 (P1-12)
    ("src.shared.backend.monitoring.metrics", "MetricsManager"),
]

def test_import(module_path, class_name):
    """测试模块导入"""
    try:
        module = __import__(module_path, fromlist=[class_name])
        if hasattr(module, class_name):
            print(f"✓ {module_path}.{class_name} - 导入成功")
            return True
        else:
            print(f"✗ {module_path}.{class_name} - 类未找到")
            return False
    except Exception as e:
        print(f"✗ {module_path}.{class_name} - 导入失败: {e}")
        return False

# 执行导入测试
results = []
for module_path, class_name in modules_to_test:
    success = test_import(module_path, class_name)
    results.append((f"{module_path}.{class_name}", success))

# 输出总结
print("\n" + "=" * 60)
print("导入验证结果")
print("=" * 60)

total = len(results)
passed = sum(1 for _, success in results if success)

for name, success in results:
    status = "✓" if success else "✗"
    print(f"{status} {name}")

print(f"\n总计: {passed}/{total} 个模块导入成功")

if passed == total:
    print("\n🎉 所有核心模块导入成功！")
    print("P1阶段实现代码完整性验证通过。")
    sys.exit(0)
else:
    print(f"\n⚠️  有 {total - passed} 个模块导入失败")
    print("需要检查模块依赖和环境配置。")
    sys.exit(1)