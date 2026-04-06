#!/usr/bin/env python3
"""
HackSynth LLM代理集成测试脚本
测试ClawAI AI引擎服务中的LLM代理功能
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_config_manager():
    """测试配置管理器"""
    logger.info("测试配置管理器...")

    from llm_agent.config_manager import LLMConfigManager

    # 创建配置管理器
    config_manager = LLMConfigManager()

    # 列出配置
    configs = config_manager.list_configs()
    logger.info(f"可用配置: {configs}")

    # 加载默认配置
    config = config_manager.load_config("clawai_pentest_agent")
    logger.info(f"加载配置: {config.get('name')}, 版本: {config.get('version')}")

    # 验证配置
    errors = config_manager.validate_config(config)
    if errors:
        logger.error(f"配置验证错误: {errors}")
        return False
    else:
        logger.info("配置验证通过")

    # 测试创建新配置
    new_config = config_manager.create_config_from_template("test_config", "pentest")
    logger.info(f"创建测试配置: {new_config.get('name')}")

    # 保存配置
    try:
        config_path = config_manager.save_config("test_config", new_config)
        logger.info(f"配置保存到: {config_path}")

        # 清理测试文件
        if os.path.exists(config_path):
            os.remove(config_path)
            logger.info("清理测试配置文件")
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return False

    logger.info("配置管理器测试通过 ✓")
    return True


async def test_pentest_agent():
    """测试渗透测试代理"""
    logger.info("测试渗透测试代理...")

    from llm_agent.pentest_agent import ClawAIPentestAgent
    from llm_agent.config_manager import LLMConfigManager

    # 加载配置
    config_manager = LLMConfigManager()
    config = config_manager.load_config("clawai_pentest_agent")

    # 创建代理（使用模拟工具执行URL）
    try:
        agent = ClawAIPentestAgent(
            config=config,
            tool_executor_url="http://localhost:8082",  # 模拟URL
            skill_registry=None  # 无技能注册表
        )
        logger.info(f"代理创建成功: {agent.model_id} ({agent.provider})")
    except Exception as e:
        logger.error(f"代理创建失败: {e}")
        return False

    # 测试代理方法
    target = "example.com"
    scan_results = {"ports": [80, 443], "services": {"80": "http", "443": "https"}}
    available_skills = ["nmap", "whatweb", "sqlmap"]

    # 测试重置
    agent.reset()
    logger.info("代理重置完成")

    # 测试阶段确定
    phase = agent.determine_phase("", scan_results)
    logger.info(f"确定阶段: {phase}")

    # 测试技能选择（需要技能统计）
    best_skill = agent.select_best_skill(available_skills, {})
    logger.info(f"选择的最佳技能: {best_skill}")

    # 测试技能统计更新
    agent.update_skill_statistics("nmap", True, 10.5)
    agent.update_skill_statistics("nmap", False, 5.0)
    logger.info(f"技能统计: {agent.skill_statistics}")

    # 测试命令提取（模拟planner输出）
    test_output = "建议执行端口扫描: <CMD>nmap -sS example.com</CMD>"
    command = agent.extract_command(test_output)
    logger.info(f"提取的命令: {command}")

    # 测试工具识别
    tool_name = agent._identify_tool_from_command("nmap -sS example.com")
    logger.info(f"识别的工具: {tool_name}")

    logger.info("渗透测试代理基本功能测试通过 ✓")
    return True


async def test_integrator():
    """测试集成器"""
    logger.info("测试LLM代理集成器...")

    from llm_agent.integrations import LLMAgentIntegrator
    from llm_agent.config_manager import LLMConfigManager

    # 创建集成器
    config_manager = LLMConfigManager()
    integrator = LLMAgentIntegrator(config_manager=config_manager)

    # 测试列出配置
    configs = integrator.list_available_configs()
    logger.info(f"集成器可用配置: {len(configs)} 个")

    # 测试创建代理
    try:
        agent = integrator.create_agent("clawai_pentest_agent")
        logger.info(f"通过集成器创建代理成功: {agent.__class__.__name__}")
    except Exception as e:
        logger.error(f"创建代理失败: {e}")
        return False

    # 测试目标分析（模拟，不实际调用LLM）
    logger.info("注意: 目标分析测试需要LLM API密钥，跳过实际调用")

    logger.info("LLM代理集成器基本功能测试通过 ✓")
    return True


async def test_enhanced_config():
    """测试增强版配置"""
    logger.info("测试增强版配置...")

    from llm_agent.config_manager import LLMConfigManager

    config_manager = LLMConfigManager()

    # 检查增强版配置是否存在
    configs = config_manager.list_configs()
    if "hacksynth_enhanced" not in configs:
        logger.warning("增强版配置不存在，将创建...")
        # 可以在此处创建，但我们已经创建了文件
        # 重新列出配置
        configs = config_manager.list_configs()

    if "hacksynth_enhanced" in configs:
        # 加载增强版配置
        enhanced_config = config_manager.load_config("hacksynth_enhanced")
        logger.info(f"加载增强版配置: {enhanced_config.get('name')}, 版本: {enhanced_config.get('version')}")

        # 验证配置
        errors = config_manager.validate_config(enhanced_config)
        if errors:
            logger.error(f"增强版配置验证错误: {errors}")
            return False

        # 检查新字段
        has_skill_mapping = "skill_mapping" in enhanced_config
        has_phases = "phases" in enhanced_config
        has_target_types = "target_types" in enhanced_config

        logger.info(f"增强版配置特性:")
        logger.info(f"  - 技能映射: {has_skill_mapping}")
        logger.info(f"  - 阶段定义: {has_phases}")
        logger.info(f"  - 目标类型: {has_target_types}")

        if has_skill_mapping:
            skills = list(enhanced_config["skill_mapping"].keys())
            logger.info(f"  - 定义技能: {len(skills)} 个")

        logger.info("增强版配置测试通过 ✓")
        return True
    else:
        logger.error("增强版配置未找到")
        return False


async def run_all_tests():
    """运行所有测试"""
    logger.info("=" * 60)
    logger.info("开始 HackSynth LLM代理集成测试")
    logger.info("=" * 60)

    test_results = {}

    # 测试配置管理器
    test_results["config_manager"] = await test_config_manager()

    # 测试渗透测试代理
    test_results["pentest_agent"] = await test_pentest_agent()

    # 测试集成器
    test_results["integrator"] = await test_integrator()

    # 测试增强版配置
    test_results["enhanced_config"] = await test_enhanced_config()

    # 汇总结果
    logger.info("=" * 60)
    logger.info("测试结果汇总:")
    logger.info("=" * 60)

    all_passed = True
    for test_name, passed in test_results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        logger.info(f"{test_name:20} {status}")
        if not passed:
            all_passed = False

    logger.info("=" * 60)
    if all_passed:
        logger.info("所有测试通过! HackSynth LLM代理集成基本功能正常。")
    else:
        logger.warning("部分测试失败，请检查相关问题。")

    return all_passed


async def quick_integration_check():
    """快速集成检查"""
    logger.info("执行快速集成检查...")

    # 检查关键文件是否存在
    required_files = [
        "llm_agent/config_manager.py",
        "llm_agent/pentest_agent.py",
        "llm_agent/integrations.py",
        "configs/clawai_pentest_agent.json"
    ]

    base_dir = os.path.dirname(os.path.abspath(__file__))

    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            logger.info(f"✓ {file_path}")
        else:
            logger.error(f"✗ {file_path} 不存在")
            return False

    # 检查模块导入
    try:
        from llm_agent.config_manager import LLMConfigManager
        from llm_agent.pentest_agent import ClawAIPentestAgent
        from llm_agent.integrations import LLMAgentIntegrator
        logger.info("✓ 所有关键模块可导入")
    except ImportError as e:
        logger.error(f"✗ 模块导入失败: {e}")
        return False

    logger.info("快速集成检查通过 ✓")
    return True


if __name__ == "__main__":
    # 运行快速检查
    quick_ok = asyncio.run(quick_integration_check())

    if quick_ok:
        logger.info("快速检查通过，开始完整测试...")
        # 运行完整测试
        asyncio.run(run_all_tests())
    else:
        logger.error("快速检查失败，跳过完整测试")
        sys.exit(1)