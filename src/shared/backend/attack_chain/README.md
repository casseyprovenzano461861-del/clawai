# 攻击链生成器 (Attack Chain Builder)

## 概述

攻击链生成器是一个根据扫描结果自动生成可展示攻击路径的工具。它将技术扫描结果转化为易于理解的攻击步骤，为安全测试提供清晰的攻击路线图。

## 功能特性

- **智能生成攻击链**：根据扫描结果自动生成攻击步骤
- **中文描述**：所有步骤描述均为中文，便于展示
- **AI集成支持**：支持DeepSeek API生成描述（模拟）
- **回退机制**：AI不可用时使用规则生成描述
- **最大10步限制**：防止攻击链过长
- **JSON输出**：标准化输出格式
- **多工具支持**：支持nmap、whatweb、nuclei、sqlmap、wpscan等

## 安装与使用

### 基本使用

```python
from builder import AttackChainBuilder

# 创建攻击链生成器
builder = AttackChainBuilder()

# 生成示例攻击链
result = builder.build_from_example()
print(result)
```

### 使用自定义上下文

```python
# 自定义扫描结果
custom_context = {
    "results": {
        "nmap": {
            "ports": [
                {"port": 80, "service": "http", "state": "open"},
                {"port": 443, "service": "https", "state": "open"}
            ]
        },
        "whatweb": {
            "fingerprint": {
                "web_server": "nginx",
                "cms": ["WordPress"]
            }
        }
    }
}

# 生成攻击链
result = builder.build_chain(custom_context)
```

### 命令行使用

```bash
# 生成示例攻击链
python builder.py --example

# 从文件读取上下文
python builder.py --context scan_results.json

# 从标准输入读取
echo '{"results": {...}}' | python builder.py
```

## 输入格式

```json
{
    "results": {
        "nmap": {
            "ports": [
                {"port": 80, "service": "http", "state": "open"},
                {"port": 443, "service": "https", "state": "open"}
            ]
        },
        "whatweb": {
            "fingerprint": {
                "web_server": "nginx",
                "language": ["PHP"],
                "cms": ["WordPress"],
                "other": []
            }
        },
        "nuclei": {
            "vulnerabilities": [
                {"name": "WordPress XSS", "severity": "medium"}
            ]
        }
    }
}
```

## 输出格式

```json
{
    "attack_chain": [
        {
            "step": 1,
            "tool": "nmap",
            "description": "发现80, 443端口开放，其中包含Web服务端口"
        },
        {
            "step": 2,
            "tool": "whatweb",
            "description": "识别为WordPress系统"
        },
        {
            "step": 3,
            "tool": "wpscan",
            "description": "发现插件漏洞"
        },
        {
            "step": 4,
            "tool": "exploit",
            "description": "可能实现远程代码执行"
        }
    ]
}
```

## 支持的工具

| 工具 | 中文名称 | 描述 |
|------|----------|------|
| nmap | 端口扫描 | 发现开放端口和服务 |
| whatweb | Web指纹识别 | 识别Web技术栈 |
| nuclei | 漏洞扫描 | 检测已知安全漏洞 |
| sqlmap | SQL注入检测 | 寻找数据库注入漏洞 |
| wpscan | WordPress扫描 | 检测WordPress插件和主题漏洞 |
| httpx | HTTP服务探测 | 发现可用资产 |
| dirsearch | 目录爆破 | 发现隐藏路径 |
| exploit | 漏洞利用 | 利用发现的漏洞进行攻击 |

## 智能决策逻辑

1. **起始工具**：按nmap → whatweb → nuclei → sqlmap → wpscan顺序选择
2. **WordPress检测**：whatweb识别WordPress后，下一步推荐wpscan
3. **PHP/ASP应用**：识别PHP/ASP后，下一步推荐sqlmap
4. **漏洞利用**：发现漏洞后，下一步推荐exploit
5. **最大步骤**：攻击链最多10步，防止过长

## 与执行器集成

```python
# 模拟执行器结果
from tools.executor import ToolExecutor

# 执行扫描
executor = ToolExecutor()
scan_results = executor.execute(target, actions)

# 生成攻击链
from attack_chain.builder import AttackChainBuilder
builder = AttackChainBuilder()
attack_chain = builder.build_chain({"results": scan_results["results"]})

# 将攻击链集成到报告中
report["attack_chain"] = attack_chain["attack_chain"]
```

## 测试

运行测试套件：

```bash
python test_builder.py
```

运行使用示例：

```bash
python usage_example.py
```

## 文件结构

```
backend/attack_chain/
├── builder.py          # 攻击链生成器主文件
├── test_builder.py     # 测试文件
├── usage_example.py    # 使用示例
├── README.md          # 说明文档
└── __pycache__/       # Python缓存
```

## 注意事项

1. **AI功能**：当前版本模拟AI生成描述，实际使用时需集成真正的AI API
2. **输入验证**：确保输入数据包含正确的results字段
3. **工具支持**：仅支持已实现的工具，其他工具使用通用描述
4. **编码问题**：确保文件使用UTF-8编码

## 扩展开发

如需支持新工具，需要：

1. 在`_generate_description`方法中添加工具描述生成逻辑
2. 在`_get_next_tool`方法中添加工具执行顺序逻辑
3. 更新工具映射表（如需要）

## 许可证

MIT License