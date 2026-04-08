# -*- coding: utf-8 -*-
"""
工具 Schema 定义
定义所有可用工具的 Function Calling 格式 (OpenAI 兼容)
"""

from typing import Dict, List, Any, Optional


# ===== 信息收集类工具 =====

NMAP_SCAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "nmap_scan",
        "description": "执行端口扫描，识别开放端口和运行的服务。用于网络资产发现和服务识别。",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标IP、域名或CIDR网段，如 '192.168.1.1' 或 'example.com'"
                },
                "ports": {
                    "type": "string",
                    "description": "端口范围，如 '1-1000' 或 '80,443,8080,3306'。默认扫描常用端口"
                },
                "scan_type": {
                    "type": "string",
                    "enum": ["quick", "full", "service"],
                    "default": "quick",
                    "description": "扫描类型：quick-快速扫描常用端口，full-全端口扫描，service-服务版本识别"
                }
            },
            "required": ["target"]
        }
    }
}

WHATWEB_SCAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "whatweb_scan",
        "description": "Web技术栈指纹识别，识别CMS、Web框架、服务器类型、JavaScript库等",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标URL，如 'https://example.com'"
                }
            },
            "required": ["target"]
        }
    }
}

SUBFINDER_SCAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "subfinder_scan",
        "description": "被动子域名枚举，从多个来源收集子域名信息",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "目标域名，如 'example.com'"
                }
            },
            "required": ["domain"]
        }
    }
}

DIRSEARCH_SCAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "dirsearch_scan",
        "description": "目录和文件爆破，发现隐藏的路径和文件",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标URL，如 'https://example.com'"
                },
                "extensions": {
                    "type": "string",
                    "default": "php,html,js,txt,bak",
                    "description": "要扫描的文件扩展名"
                },
                "threads": {
                    "type": "integer",
                    "default": 10,
                    "description": "并发线程数"
                }
            },
            "required": ["target"]
        }
    }
}

HTTPX_PROBE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "httpx_probe",
        "description": "HTTP探测与存活检测，批量检测目标是否存活并获取基本信息",
        "parameters": {
            "type": "object",
            "properties": {
                "targets": {
                    "type": "string",
                    "description": "目标列表，可以是文件路径或逗号分隔的目标"
                }
            },
            "required": ["targets"]
        }
    }
}


# ===== 漏洞扫描类工具 =====

NUCLEI_SCAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "nuclei_scan",
        "description": "基于模板的漏洞扫描，检测CVE、常见漏洞和配置问题。支持数千个模板",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标URL或IP"
                },
                "templates": {
                    "type": "string",
                    "description": "模板目录或标签，如 'cves/' 或 'vulnerabilities/'"
                },
                "severity": {
                    "type": "string",
                    "description": "严重级别过滤，如 'high,critical'"
                }
            },
            "required": ["target"]
        }
    }
}

SQLMAP_SCAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "sqlmap_scan",
        "description": "SQL注入漏洞检测和利用。自动检测和利用SQL注入漏洞",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标URL，如 'http://example.com/page?id=1'"
                },
                "data": {
                    "type": "string",
                    "description": "POST数据"
                },
                "level": {
                    "type": "integer",
                    "default": 1,
                    "description": "测试级别(1-5)，级别越高检测越全面但越慢"
                },
                "risk": {
                    "type": "integer",
                    "default": 1,
                    "description": "风险级别(1-3)，高级别可能触发更多检测"
                }
            },
            "required": ["target"]
        }
    }
}

NIKTO_SCAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "nikto_scan",
        "description": "Web服务器漏洞扫描器，检测服务器配置问题和已知漏洞",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标URL"
                }
            },
            "required": ["target"]
        }
    }
}

XSSTRIKE_SCAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "xsstrike_scan",
        "description": "XSS漏洞检测工具，检测跨站脚本漏洞",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标URL"
                }
            },
            "required": ["target"]
        }
    }
}


# ===== CMS扫描类工具 =====

WPSCAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "wpscan",
        "description": "WordPress漏洞扫描器，检测WordPress版本、插件和主题漏洞",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "WordPress站点URL"
                },
                "enumerate": {
                    "type": "string",
                    "default": "vp,vt,u",
                    "description": "枚举选项：vp-易受攻击插件, vt-易受攻击主题, u-用户"
                }
            },
            "required": ["target"]
        }
    }
}


# ===== 密码破解类工具 =====

HYDRA_BRUTE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "hydra_brute",
        "description": "网络登录暴力破解，支持多种协议的密码破解",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标地址"
                },
                "service": {
                    "type": "string",
                    "description": "服务类型，如 'ssh', 'ftp', 'http-post-form'"
                },
                "user": {
                    "type": "string",
                    "description": "用户名或用户名字典文件"
                },
                "pass": {
                    "type": "string",
                    "description": "密码或密码字典文件"
                }
            },
            "required": ["target", "service"]
        }
    }
}


# ===== SSL/TLS 安全检测 =====

TESTSSL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "testssl_scan",
        "description": "SSL/TLS安全检测，检查证书、协议和加密套件配置",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标地址:端口，如 'example.com:443'"
                }
            },
            "required": ["target"]
        }
    }
}


# ===== 渗透测试流程类工具 =====

START_PENTEST_SCHEMA = {
    "type": "function",
    "function": {
        "name": "start_pentest",
        "description": "启动完整的自动化渗透测试流程（P-E-R模式）。系统会自动执行信息收集、漏洞扫描、漏洞利用等阶段",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标地址（IP、域名或URL）"
                },
                "goal": {
                    "type": "string",
                    "description": "测试目标描述，如 '对目标进行Web渗透测试'"
                },
                "mode": {
                    "type": "string",
                    "enum": ["recon", "vuln_scan", "full"],
                    "default": "full",
                    "description": "测试模式：recon-仅信息收集，vuln_scan-信息收集+漏洞扫描，full-完整渗透测试"
                }
            },
            "required": ["target"]
        }
    }
}

GET_PENTEST_STATUS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_pentest_status",
        "description": "获取当前渗透测试的执行状态、进度和已发现的信息",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}

STOP_PENTEST_SCHEMA = {
    "type": "function",
    "function": {
        "name": "stop_pentest",
        "description": "停止当前正在进行的渗透测试",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}


# ===== 报告类工具 =====

GENERATE_REPORT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "generate_report",
        "description": "生成渗透测试报告，包含漏洞详情、风险评级和修复建议",
        "parameters": {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "enum": ["html", "pdf", "json", "markdown"],
                    "default": "html",
                    "description": "报告格式"
                },
                "include_evidence": {
                    "type": "boolean",
                    "default": True,
                    "description": "是否包含证据截图和详细输出"
                }
            }
        }
    }
}


# ===== 系统控制类工具 =====

GET_TOOL_STATUS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_tool_status",
        "description": "获取所有工具的安装状态和可用性",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}


# ===== 完整工具列表 =====

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    # 信息收集类
    NMAP_SCAN_SCHEMA,
    WHATWEB_SCAN_SCHEMA,
    SUBFINDER_SCAN_SCHEMA,
    DIRSEARCH_SCAN_SCHEMA,
    HTTPX_PROBE_SCHEMA,
    
    # 漏洞扫描类
    NUCLEI_SCAN_SCHEMA,
    SQLMAP_SCAN_SCHEMA,
    NIKTO_SCAN_SCHEMA,
    XSSTRIKE_SCAN_SCHEMA,
    
    # CMS扫描类
    WPSCAN_SCHEMA,
    
    # 密码破解类
    HYDRA_BRUTE_SCHEMA,
    
    # SSL检测
    TESTSSL_SCHEMA,
    
    # 渗透测试流程
    START_PENTEST_SCHEMA,
    GET_PENTEST_STATUS_SCHEMA,
    STOP_PENTEST_SCHEMA,
    
    # 报告生成
    GENERATE_REPORT_SCHEMA,
    
    # 系统控制
    GET_TOOL_STATUS_SCHEMA,
]


# ===== 新增工具 Schema（阶段5扩展）=====

FFUF_SCAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "ffuf_scan",
        "description": "高性能模糊测试工具，支持目录、DNS、子域名等多种模式",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标URL或域名"
                },
                "mode": {
                    "type": "string",
                    "enum": ["dir", "dns", "vhost", "fuzz"],
                    "default": "dir",
                    "description": "模糊测试模式：dir-目录爆破, dns-DNS枚举, vhost-虚拟主机, fuzz-自定义"
                },
                "wordlist": {
                    "type": "string",
                    "default": "common.txt",
                    "description": "字典文件名称或路径"
                },
                "threads": {
                    "type": "integer",
                    "default": 40,
                    "description": "并发线程数"
                }
            },
            "required": ["target"]
        }
    }
}

NAABU_SCAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "naabu_scan",
        "description": "快速端口扫描工具，支持SYN扫描和Connect扫描",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标IP、域名或CIDR"
                },
                "ports": {
                    "type": "string",
                    "description": "端口范围，如 '1-65535' 或 'top100'"
                },
                "scan_type": {
                    "type": "string",
                    "enum": ["syn", "connect"],
                    "default": "syn",
                    "description": "扫描类型"
                }
            },
            "required": ["target"]
        }
    }
}

MASSDNS_SCAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "massdns_scan",
        "description": "高性能DNS解析工具，用于大规模域名解析",
        "parameters": {
            "type": "object",
            "properties": {
                "domains": {
                    "type": "string",
                    "description": "域名列表文件路径或逗号分隔的域名"
                },
                "resolvers": {
                    "type": "string",
                    "description": "DNS解析器列表文件"
                }
            },
            "required": ["domains"]
        }
    }
}

DNSX_SCAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "dnsx_scan",
        "description": "DNS工具包，支持DNS查询、区域传输检测等",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "目标域名"
                },
                "record_type": {
                    "type": "string",
                    "enum": ["A", "AAAA", "CNAME", "MX", "TXT", "NS", "SOA", "ALL"],
                    "default": "A",
                    "description": "DNS记录类型"
                }
            },
            "required": ["domain"]
        }
    }
}

GAU_SCAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "gau_scan",
        "description": "从Wayback Machine、Common Crawl等获取历史URL",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "目标域名"
                },
                "providers": {
                    "type": "string",
                    "default": "wayback,commoncrawl",
                    "description": "数据源提供者"
                }
            },
            "required": ["domain"]
        }
    }
}

NUCLEI_TAGS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "nuclei_tags",
        "description": "获取Nuclei可用的模板标签列表",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}

SEARCHSPLOIT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "searchsploit",
        "description": "搜索Exploit-DB中的漏洞利用代码",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，如服务名称、CVE编号等"
                },
                "exact": {
                    "type": "boolean",
                    "default": False,
                    "description": "是否精确匹配"
                }
            },
            "required": ["query"]
        }
    }
}


# ===== 扩展后的完整工具列表 =====

EXTENDED_TOOL_SCHEMAS: List[Dict[str, Any]] = TOOL_SCHEMAS + [
    # 新增信息收集工具
    FFUF_SCAN_SCHEMA,
    NAABU_SCAN_SCHEMA,
    MASSDNS_SCAN_SCHEMA,
    DNSX_SCAN_SCHEMA,
    GAU_SCAN_SCHEMA,
    
    # 新增漏洞利用工具
    SEARCHSPLOIT_SCHEMA,
    
    # 辅助工具
    NUCLEI_TAGS_SCHEMA,
]


def get_tool_schema(tool_name: str) -> Optional[Dict[str, Any]]:
    """根据工具名称获取对应的 Schema
    
    Args:
        tool_name: 工具名称
        
    Returns:
        工具 Schema，如果不存在则返回 None
    """
    for schema in TOOL_SCHEMAS:
        if schema.get("function", {}).get("name") == tool_name:
            return schema
    return None


def get_tools_by_category() -> Dict[str, List[str]]:
    """按类别获取工具列表
    
    Returns:
        类别到工具名称列表的映射
    """
    return {
        "信息收集": ["nmap_scan", "whatweb_scan", "subfinder_scan", "dirsearch_scan", "httpx_probe"],
        "漏洞扫描": ["nuclei_scan", "sqlmap_scan", "nikto_scan", "xsstrike_scan"],
        "CMS扫描": ["wpscan"],
        "密码破解": ["hydra_brute"],
        "SSL检测": ["testssl_scan"],
        "渗透测试": ["start_pentest", "get_pentest_status", "stop_pentest"],
        "报告生成": ["generate_report"],
        "系统控制": ["get_tool_status"]
    }


def get_all_tool_names() -> List[str]:
    """获取所有工具名称列表
    
    Returns:
        工具名称列表
    """
    return [schema["function"]["name"] for schema in TOOL_SCHEMAS]
