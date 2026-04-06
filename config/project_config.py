# -*- coding: utf-8 -*-
"""
ClawAI - 项目配置模块
技术诚信重建：明确项目定位
"""

PROJECT_CONFIG = {
    "name": "ClawAI - 智能安全评估系统",
    "version": "2.0",
    "description": "基于规则引擎和AI辅助的安全评估工具",
    "features": {
        "ai_assisted": True,      # AI辅助决策，不是AI驱动
        "rule_based": True,       # 基于规则的智能决策
        "tool_integration": True, # 真实工具集成
        "automation": True        # 自动化工作流
    },
    "transparency": {
        "ai_capabilities": "辅助分析，非完全自主决策",
        "tool_coverage": "核心工具已集成，部分工具需手动安装",
        "security_level": "企业级安全防护"
    },
    "technical_honesty": {
        "ai_limitations": "明确告知AI辅助功能的局限性",
        "tool_requirements": "诚实地告知所需的工具安装",
        "real_execution": "所有工具调用均为真实执行，非模拟",
        "capability_boundaries": "清晰地定义系统能力的边界"
    }
}


def get_project_info():
    """获取项目信息"""
    return {
        "name": PROJECT_CONFIG["name"],
        "version": PROJECT_CONFIG["version"],
        "description": PROJECT_CONFIG["description"],
        "technical_positioning": "基于规则引擎和AI辅助的安全评估工具",
        "core_philosophy": "技术诚信 - 诚实地告知系统能力边界"
    }


def get_features_status():
    """获取功能状态"""
    return PROJECT_CONFIG["features"]


def get_transparency_info():
    """获取透明度信息"""
    return PROJECT_CONFIG["transparency"]


def get_technical_honesty():
    """获取技术诚信声明"""
    return PROJECT_CONFIG["technical_honesty"]


def print_project_config():
    """打印项目配置"""
    print("=" * 80)
    print("ClawAI 项目配置")
    print("=" * 80)
    
    info = get_project_info()
    print(f"项目名称: {info['name']}")
    print(f"版本: {info['version']}")
    print(f"描述: {info['description']}")
    print(f"技术定位: {info['technical_positioning']}")
    print(f"核心哲学: {info['core_philosophy']}")
    
    print("\n功能状态:")
    features = get_features_status()
    for feature, enabled in features.items():
        status = "✓" if enabled else "✗"
        print(f"  {status} {feature}")
    
    print("\n透明度信息:")
    transparency = get_transparency_info()
    for key, value in transparency.items():
        print(f"  {key}: {value}")
    
    print("\n技术诚信声明:")
    honesty = get_technical_honesty()
    for key, value in honesty.items():
        print(f"  {key}: {value}")
    
    print("=" * 80)


if __name__ == "__main__":
    print_project_config()