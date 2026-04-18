# CTF 基准测试框架快速开始指南

基于 HackSynth 架构的 CTF 基准测试框架，用于评估 AI 代理在渗透测试任务上的表现。

## 🚀 快速开始

### 1. 环境准备

确保已安装以下依赖：
- Python 3.8+
- Docker & Docker Compose
- Git

### 2. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt  # 如果存在 requirements.txt 文件

# 或安装核心依赖
pip install pyyaml pandas numpy matplotlib
```

### 3. 验证挑战配置

```bash
# 验证单个挑战文件
python scripts/validate_challenge.py picoctf/challenges/picoctf-2023-warmup.yaml

# 验证整个目录
python scripts/validate_challenge.py picoctf/challenges/ --summary
```

### 4. 运行基准测试

```bash
# 运行 PicoCTF 初级基准测试
python scripts/benchmark_runner.py --config picoctf/configs/picoctf-beginner-benchmark.yaml

# 运行 OverTheWire 初级基准测试
python scripts/benchmark_runner.py --config overthewire/configs/overthewire-beginner-benchmark.yaml
```

### 5. 分析结果

```bash
# 分析单个结果文件
python scripts/result_analyzer.py --results results/picoctf-beginner/YYYYMMDD_HHMMSS.json

# 分析多个结果文件
python scripts/result_analyzer.py --results results/picoctf-beginner/*.json
```

### 6. 生成报告

```bash
# 生成 HTML 报告
python scripts/report_generator.py --input analysis/YYYYMMDD_HHMMSS.json --format html

# 生成 Markdown 报告
python scripts/report_generator.py --input analysis/YYYYMMDD_HHMMSS.json --format markdown
```

## 📁 目录结构

```
ctf_benchmarks/
├── config/                          # 框架全局配置
│   └── benchmark_config.yaml       # 主配置文件
├── picoctf/                        # PicoCTF 平台
│   ├── challenges/                 # 挑战定义文件
│   │   ├── picoctf-2023-warmup.yaml
│   │   ├── picoctf-2019-insp3ct0r.yaml
│   │   ├── picoctf-2019-dont-use-client-side.yaml
│   │   └── picoctf-2019-logon.yaml
│   ├── configs/                    # 基准测试配置
│   │   └── picoctf-beginner-benchmark.yaml
│   └── scripts/                    # 平台特定脚本
├── overthewire/                    # OverTheWire 平台
│   ├── challenges/                 # 挑战定义文件
│   │   ├── overthewire-bandit-level0.yaml
│   │   ├── overthewire-bandit-level1.yaml
│   │   ├── overthewire-natas-level0.yaml
│   │   └── overthewire-natas-level1.yaml
│   ├── configs/                    # 基准测试配置
│   │   └── overthewire-beginner-benchmark.yaml
│   └── scripts/                    # 平台特定脚本
├── scripts/                        # 核心脚本
│   ├── benchmark_runner.py         # 基准测试运行器
│   ├── result_analyzer.py          # 结果分析器
│   ├── report_generator.py         # 报告生成器
│   └── validate_challenge.py       # 挑战验证器
├── results/                        # 基准测试结果
│   ├── picoctf-beginner/           # PicoCTF 初级结果
│   └── overthewire-beginner/       # OverTheWire 初级结果
├── reports/                        # 生成的报告
├── docs/                           # 文档
│   └── challenge_format.md         # 挑战格式规范
└── QUICKSTART.md                   # 本文件
```

## 🎯 包含的挑战

### PicoCTF 挑战 (4个)
1. **Warm Up** (`picoctf-2023-warmup`) - 非常容易
   - 类别: Web
   - 技能: HTML 源代码分析
   - 标志: 隐藏在 HTML 注释中

2. **Insp3ct0r** (`picoctf-2019-insp3ct0r`) - 容易
   - 类别: Web
   - 技能: HTML/CSS/JS 文件分析
   - 标志: 分割在三个文件中

3. **Don't Use Client Side** (`picoctf-2019-dont-use-client-side`) - 容易
   - 类别: Web
   - 技能: JavaScript 逆向工程
   - 标志: 客户端验证绕过

4. **Logon** (`picoctf-2019-logon`) - 容易
   - 类别: Web
   - 技能: Cookie 操作和会话管理
   - 标志: 认证绕过

### OverTheWire 挑战 (4个)
1. **Bandit Level 0** (`overthewire-bandit-level0`) - 非常容易
   - 类别: Linux
   - 技能: SSH 连接和基本命令
   - 标志: 读取文件内容

2. **Bandit Level 1** (`overthewire-bandit-level1`) - 容易
   - 类别: Linux
   - 技能: 特殊文件名处理
   - 标志: 读取名为 "-" 的文件

3. **Natas Level 0** (`overthewire-natas-level0`) - 非常容易
   - 类别: Web
   - 技能: HTTP 基础认证
   - 标志: 页面源代码分析

4. **Natas Level 1** (`overthewire-natas-level1`) - 容易
   - 类别: Web
   - 技能: 绕过右键点击限制
   - 标志: 查看源代码绕过 JavaScript 限制

## 🔧 配置说明

### 挑战配置文件格式
挑战使用 YAML 格式定义，包含以下主要部分：

```yaml
id: "picoctf-2023-warmup"          # 唯一标识符
name: "Warm Up"                    # 挑战名称
platform: "picoctf"                # 平台
category: "web"                    # 类别
difficulty: "very_easy"            # 难度
points: 100                        # 分值
description: "挑战描述..."         # 详细描述
hints: ["提示1", "提示2"]          # 提示列表
solution: "picoCTF{...}"           # 解决方案
validation_regex: "picoCTF\\{.*\\}" # 验证正则表达式
test_cases: [...]                  # 测试用例
metrics: {...}                     # 评估指标
container_config: {...}            # 容器配置
agent_config: {...}                # AI 代理配置
```

### 基准测试配置文件格式
基准测试配置定义要运行的挑战集合和评估参数：

```yaml
name: "picoctf-beginner-benchmark"
platform: "picoctf"
difficulty: "beginner"
challenges:                         # 挑战列表
  - id: "picoctf-2023-warmup"
    weight: 1.0
    enabled: true
    timeout: 300
parameters: {...}                   # 基准测试参数
metrics: {...}                      # 评估指标配置
scoring: {...}                      # 评分系统
agent_configs: {...}                # AI 代理配置
```

## 🤖 AI 代理集成

框架支持多种 AI 代理架构：

### 1. HackSynth 双模块代理
- **Planner 模块**: 生成渗透测试命令
- **Summarizer 模块**: 总结执行结果
- 迭代优化策略

### 2. 单模块代理
- 直接生成命令并执行
- 简单但有效

### 3. 多代理协作
- 研究员代理 + 执行者代理
- 分工合作

### 配置示例
```yaml
agent_config:
  llm_provider: "deepseek"
  llm_model: "deepseek-chat"
  temperature: 0.7
  max_tokens: 1024
  
  observation_space:
    type: "text"
    max_length: 4096
    
  action_space:
    type: "command"
    allowed_commands: ["curl", "grep", "ls", "cat"]
    
  reward_function:
    base_reward: 0
    flag_found: 100
    step_penalty: -1
```

## 📊 评估指标

### 主要指标
1. **成功率**: 完成挑战的比例
2. **平均步数**: 解决挑战所需的平均命令数
3. **平均时间**: 解决挑战所需的平均时间
4. **Token 效率**: 每成功挑战消耗的 Token 数

### 辅助指标
1. **命令多样性**: 使用不同命令的比例
2. **错误率**: 无效命令的比例
3. **学习曲线**: 随时间进步的速度
4. **技能覆盖率**: 掌握的技能比例

## 🔄 工作流程

```
1. 配置挑战和基准测试
   ↓
2. 验证配置格式和完整性
   ↓
3. 运行基准测试（模拟或实际 AI 代理）
   ↓
4. 收集执行结果和指标
   ↓
5. 分析结果并生成统计报告
   ↓
6. 生成可视化报告和建议
```

## 🛠️ 扩展框架

### 添加新挑战
1. 在对应平台的 `challenges/` 目录创建 YAML 文件
2. 遵循挑战格式规范
3. 使用验证脚本检查格式
4. 添加到基准测试配置中

### 添加新平台
1. 创建平台目录结构
2. 实现平台接口（如果需要）
3. 更新全局配置中的平台列表
4. 添加示例挑战和配置

### 添加新评估指标
1. 在指标配置中定义新指标
2. 更新结果分析器以计算指标
3. 更新报告生成器以显示指标

## 📈 示例用例

### 用例 1: 比较不同 AI 代理
```bash
# 配置不同代理参数
# 运行基准测试
# 比较成功率、效率和成本
```

### 用例 2: 评估学习能力
```bash
# 多次运行同一基准测试
# 分析学习曲线和进步速度
# 评估适应性和泛化能力
```

### 用例 3: 识别薄弱环节
```bash
# 分析各挑战的成功率
# 识别低成功率挑战类型
# 针对性改进训练数据
```

## 🔍 故障排除

### 常见问题

1. **验证失败**
   - 检查 YAML 格式是否正确
   - 验证必需字段是否完整
   - 检查字段值是否有效

2. **基准测试运行失败**
   - 检查依赖是否安装
   - 验证配置文件路径
   - 检查文件权限

3. **结果分析错误**
   - 检查结果文件格式
   - 验证数据完整性
   - 检查 Python 依赖

### 获取帮助
- 查看 `docs/` 目录中的文档
- 检查挑战格式规范
- 运行示例和测试

## 📚 参考资料

### 相关项目
- **HackSynth**: arXiv:2412.01778 - Evaluating LLM Agents for Autonomous Penetration Testing
- **PentAGI**: 微服务架构的渗透测试 AI 平台

### 数据来源
- **PicoCTF**: https://picoctf.org/ - 教育 CTF 平台
- **OverTheWire**: http://overthewire.org/ - 战争游戏平台

### 技术文档
- 挑战格式规范: `docs/challenge_format.md`
- 基准测试指南: `docs/benchmark_guide.md`

## 🆕 下一步

### 短期计划
1. 添加更多挑战（中级和高级）
2. 集成实际 AI 代理执行
3. 添加容器化环境支持
4. 完善监控和日志系统

### 长期计划
1. 支持更多 CTF 平台
2. 添加高级可视化功能
3. 集成到 CI/CD 流程
4. 建立性能基准和排行榜

---

**版本**: 1.0.0  
**最后更新**: 2026-04-05  
**维护者**: ClawAI 开发团队  
**许可证**: MIT  

*如有问题或建议，请提交 Issue 或联系开发团队。*