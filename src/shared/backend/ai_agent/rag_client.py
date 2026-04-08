# -*- coding: utf-8 -*-
"""
RAG 知识服务
提供语义检索接口，增强 AI 的专业能力
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import re

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeEntry:
    """知识条目"""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "source": self.source
        }


@dataclass
class SearchResult:
    """搜索结果"""
    entry: KnowledgeEntry
    score: float
    highlights: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry": self.entry.to_dict(),
            "score": self.score,
            "highlights": self.highlights
        }


class KnowledgeBase:
    """知识库
    
    管理渗透测试相关的知识条目
    """
    
    def __init__(self, knowledge_dir: str = None):
        """初始化知识库
        
        Args:
            knowledge_dir: 知识库目录
        """
        self.knowledge_dir = knowledge_dir or os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..", "knowledge"
        )
        
        # 知识条目存储
        self.entries: Dict[str, KnowledgeEntry] = {}
        
        # 索引
        self.keyword_index: Dict[str, List[str]] = {}
        
        # 加载知识
        self._load_knowledge()
        
        logger.info(f"知识库初始化完成，共 {len(self.entries)} 个条目")
    
    def _load_knowledge(self):
        """加载知识条目"""
        # 确保目录存在
        os.makedirs(self.knowledge_dir, exist_ok=True)
        
        # 加载 JSON 文件
        for filename in os.listdir(self.knowledge_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.knowledge_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        for item in data:
                            entry = KnowledgeEntry(
                                id=item.get("id", ""),
                                title=item.get("title", ""),
                                content=item.get("content", ""),
                                category=item.get("category", "general"),
                                tags=item.get("tags", []),
                                source=filename
                            )
                            self.entries[entry.id] = entry
                    
                except Exception as e:
                    logger.warning(f"加载知识文件失败 {filename}: {e}")
        
        # 如果没有加载到任何条目，创建默认知识
        if not self.entries:
            self._create_default_knowledge()
        
        # 构建索引
        self._build_index()
    
    def _create_default_knowledge(self):
        """创建默认知识条目"""
        default_entries = [
            KnowledgeEntry(
                id="nmap_basic",
                title="Nmap 基础扫描",
                content="""
## Nmap 基础扫描

### 常用扫描类型
- `-sT`: TCP 全连接扫描（默认）
- `-sS`: SYN 半开扫描（需要 root 权限）
- `-sU`: UDP 扫描
- `-sV`: 服务版本检测

### 端口选项
- `-p 1-1000`: 扫描指定范围
- `-p 80,443,8080`: 扫描指定端口
- `-F`: 快速扫描（常用端口）

### 输出选项
- `-oN output.txt`: 普通格式输出
- `-oX output.xml`: XML 格式输出
- `-oA output`: 所有格式输出

### 示例
```bash
nmap -sV -sC -p- 192.168.1.1
nmap -A -T4 example.com
```
""",
                category="tools",
                tags=["nmap", "扫描", "端口"]
            ),
            KnowledgeEntry(
                id="sql_injection",
                title="SQL 注入检测与利用",
                content="""
## SQL 注入检测与利用

### 检测方法
1. 单引号测试: `'` 或 `"`
2. 逻辑测试: `1=1` / `1=2`
3. 时间盲注: `SLEEP(5)` / `WAITFOR DELAY '0:0:5'`

### SQLMap 使用
```bash
# 基础检测
sqlmap -u "http://example.com/page?id=1"

# POST 数据
sqlmap -u "http://example.com/login" --data="user=admin&pass=123"

# 指定参数
sqlmap -u "http://example.com/page?id=1&cat=2" -p id

# 高级选项
sqlmap -u "http://example.com/page?id=1" --level=5 --risk=3
```

### 常见绕过
- 大小写混合: `SeLeCt`
- 编码绕过: `%53%45%4C%45%43%54`
- 注释绕过: `/*!SELECT*/`
""",
                category="vulnerabilities",
                tags=["sql注入", "注入", "web漏洞"]
            ),
            KnowledgeEntry(
                id="xss_attack",
                title="XSS 跨站脚本攻击",
                content="""
## XSS 跨站脚本攻击

### 类型
1. **反射型 XSS**: URL 参数直接输出
2. **存储型 XSS**: 恶意脚本存储在服务器
3. **DOM 型 XSS**: 客户端 JavaScript 注入

### 常见 Payload
```javascript
// 基础测试
<script>alert(1)</script>

// 绕过过滤
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<body onload=alert(1)>

// 编码绕过
<img src=x onerror="&#97;&#108;&#101;&#114;&#116;&#40;&#49;&#41;">
```

### 检测工具
- XSStrike
- XSSer
- Burp Suite Scanner
""",
                category="vulnerabilities",
                tags=["xss", "跨站脚本", "web漏洞"]
            ),
            KnowledgeEntry(
                id="pentest_methodology",
                title="渗透测试方法论",
                content="""
## 渗透测试方法论

### 标准流程
1. **信息收集 (Reconnaissance)**
   - 被动信息收集: OSINT
   - 主动信息收集: 扫描

2. **漏洞扫描 (Vulnerability Assessment)**
   - 自动化扫描
   - 手工验证

3. **漏洞利用 (Exploitation)**
   - 获取初始访问
   - 权限提升

4. **后渗透 (Post-Exploitation)**
   - 横向移动
   - 数据收集

5. **报告生成 (Reporting)**
   - 漏洞详情
   - 修复建议

### 测试类型
- 黑盒测试: 无任何信息
- 灰盒测试: 部分信息
- 白盒测试: 完全信息
""",
                category="methodology",
                tags=["方法论", "流程", "渗透测试"]
            ),
            KnowledgeEntry(
                id="common_ports",
                title="常见端口和服务",
                content="""
## 常见端口和服务

### Web 服务
- 80: HTTP
- 443: HTTPS
- 8080: HTTP 代理/备用端口
- 8443: HTTPS 备用端口

### 远程访问
- 22: SSH
- 23: Telnet
- 3389: RDP
- 5900: VNC

### 数据库
- 1433: MSSQL
- 1521: Oracle
- 3306: MySQL
- 5432: PostgreSQL
- 27017: MongoDB
- 6379: Redis

### 文件服务
- 21: FTP
- 445: SMB
- 139: NetBIOS

### 邮件服务
- 25: SMTP
- 110: POP3
- 143: IMAP
""",
                category="reference",
                tags=["端口", "服务", "参考"]
            )
        ]
        
        for entry in default_entries:
            self.entries[entry.id] = entry
    
    def _build_index(self):
        """构建关键词索引"""
        self.keyword_index.clear()
        
        for entry_id, entry in self.entries.items():
            # 从标题、内容、标签中提取关键词
            text = f"{entry.title} {entry.content} {' '.join(entry.tags)}"
            keywords = self._extract_keywords(text)
            
            for keyword in keywords:
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = []
                self.keyword_index[keyword].append(entry_id)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的分词
        text = text.lower()
        # 提取中英文词
        words = re.findall(r'[\w\u4e00-\u9fff]+', text)
        # 过滤停用词
        stop_words = {'的', '是', '在', '和', '与', '或', '等', 'the', 'a', 'an', 'is', 'are', 'was', 'were'}
        return [w for w in words if w not in stop_words and len(w) > 1]
    
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """搜索知识
        
        Args:
            query: 查询字符串
            top_k: 返回数量
            
        Returns:
            List[SearchResult]: 搜索结果
        """
        # 提取查询关键词
        query_keywords = self._extract_keywords(query)
        
        # 计算每个条目的匹配分数
        scores: Dict[str, float] = {}
        
        for keyword in query_keywords:
            if keyword in self.keyword_index:
                for entry_id in self.keyword_index[keyword]:
                    scores[entry_id] = scores.get(entry_id, 0) + 1
        
        # 排序并返回结果
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]
        
        results = []
        for entry_id in sorted_ids:
            entry = self.entries.get(entry_id)
            if entry:
                # 归一化分数
                score = min(1.0, scores[entry_id] / max(len(query_keywords), 1))
                
                # 生成高亮
                highlights = self._generate_highlights(entry, query_keywords)
                
                results.append(SearchResult(
                    entry=entry,
                    score=score,
                    highlights=highlights
                ))
        
        return results
    
    def _generate_highlights(
        self,
        entry: KnowledgeEntry,
        keywords: List[str]
    ) -> List[str]:
        """生成高亮片段"""
        highlights = []
        content = entry.content
        
        for keyword in keywords[:3]:
            # 查找关键词位置
            idx = content.lower().find(keyword.lower())
            if idx >= 0:
                # 提取前后各50个字符
                start = max(0, idx - 50)
                end = min(len(content), idx + len(keyword) + 50)
                highlight = content[start:end].strip()
                highlights.append(highlight)
        
        return highlights
    
    def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """获取指定条目"""
        return self.entries.get(entry_id)
    
    def get_entries_by_category(self, category: str) -> List[KnowledgeEntry]:
        """按类别获取条目"""
        return [e for e in self.entries.values() if e.category == category]
    
    def get_all_categories(self) -> List[str]:
        """获取所有类别"""
        return list(set(e.category for e in self.entries.values()))


class RAGClient:
    """RAG 客户端
    
    提供统一的语义检索接口
    """
    
    def __init__(self, knowledge_base: KnowledgeBase = None):
        """初始化 RAG 客户端
        
        Args:
            knowledge_base: 知识库实例
        """
        self.knowledge_base = knowledge_base or KnowledgeBase()
    
    def query(
        self,
        query: str,
        top_k: int = 3,
        category_filter: str = None
    ) -> List[Dict[str, Any]]:
        """查询知识
        
        Args:
            query: 查询字符串
            top_k: 返回数量
            category_filter: 类别过滤
            
        Returns:
            List[Dict]: 查询结果
        """
        results = self.knowledge_base.search(query, top_k=top_k)
        
        if category_filter:
            results = [r for r in results if r.entry.category == category_filter]
        
        return [r.to_dict() for r in results]
    
    def get_context_for_task(
        self,
        task_description: str,
        target_type: str = None
    ) -> str:
        """获取任务相关的知识上下文
        
        Args:
            task_description: 任务描述
            target_type: 目标类型
            
        Returns:
            str: 相关知识上下文
        """
        results = self.query(task_description, top_k=2)
        
        if not results:
            return ""
        
        context_parts = ["## 相关知识"]
        
        for i, result in enumerate(results, 1):
            entry = result["entry"]
            context_parts.append(f"\n### {entry['title']}")
            
            # 截取内容摘要
            content = entry["content"]
            if len(content) > 500:
                content = content[:500] + "..."
            
            context_parts.append(content)
        
        return "\n".join(context_parts)
    
    def suggest_tools(self, task_type: str) -> List[str]:
        """建议工具
        
        Args:
            task_type: 任务类型
            
        Returns:
            List[str]: 建议的工具列表
        """
        tool_mapping = {
            "port_scan": ["nmap_scan", "masscan_scan"],
            "web_scan": ["nuclei_scan", "nikto_scan", "whatweb_scan"],
            "vuln_scan": ["nuclei_scan", "sqlmap_scan", "xsstrike_scan"],
            "dir_brute": ["dirsearch_scan", "gobuster_scan", "ffuf_scan"],
            "subdomain": ["subfinder_scan", "amass_scan"],
            "exploit": ["metasploit", "searchsploit"]
        }
        
        return tool_mapping.get(task_type, [])


# ==================== 便捷函数 ====================

def create_rag_client(knowledge_dir: str = None) -> RAGClient:
    """创建 RAG 客户端
    
    Args:
        knowledge_dir: 知识库目录
        
    Returns:
        RAGClient: 客户端实例
    """
    kb = KnowledgeBase(knowledge_dir)
    return RAGClient(kb)


# ==================== 测试 ====================

def test_rag_client():
    """测试 RAG 客户端"""
    print("=" * 60)
    print("RAG 知识服务测试")
    print("=" * 60)
    
    client = create_rag_client()
    
    # 测试搜索
    print("\n1. 搜索测试:")
    results = client.query("SQL注入", top_k=3)
    print(f"  搜索结果: {len(results)} 条")
    for r in results:
        print(f"  - {r['entry']['title']} (分数: {r['score']:.2f})")
    
    # 测试上下文获取
    print("\n2. 上下文获取测试:")
    context = client.get_context_for_task("对目标进行Web漏洞扫描")
    print(context[:300] + "...")
    
    # 测试工具建议
    print("\n3. 工具建议测试:")
    tools = client.suggest_tools("web_scan")
    print(f"  建议工具: {tools}")
    
    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    test_rag_client()
