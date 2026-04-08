# ClawAI API 文档

## 1. 概述

ClawAI 提供了丰富的 RESTful API 接口，用于系统管理、工具执行、漏洞管理等功能。本文档详细介绍了所有可用的 API 端点、参数、返回值等信息。

### 1.1 基础信息

- **API 基础路径**：`http://localhost:8000`
- **认证方式**：JWT Token（可选，可通过 `DISABLE_AUTH=1` 环境变量禁用）
- **请求格式**：JSON
- **响应格式**：JSON
- **错误处理**：标准 HTTP 状态码 + 错误信息

### 1.2 版本信息

- **API 版本**：v1
- **系统版本**：2.0.0
- **文档版本**：2.0.0

## 2. 核心 API

### 2.1 健康检查

#### `GET /health`

**描述**：检查系统健康状态

**响应**：
```json
{
  "status": "healthy",
  "services": {
    "database": {
      "status": "healthy",
      "connection": "ok"
    },
    "tools": {
      "status": "healthy",
      "count": 29
    }
  },
  "version": "2.0.0"
}
```

### 2.2 工具列表

#### `GET /tools`

**描述**：获取系统集成的工具列表

**响应**：
```json
{
  "tools": [
    {
      "name": "nmap",
      "description": "网络扫描工具"
    },
    {
      "name": "sqlmap",
      "description": "SQL注入工具"
    }
  ],
  "categories": {
    "network_scanner": "网络扫描工具",
    "web_scanner": "Web扫描工具"
  },
  "count": 29
}
```

### 2.3 执行攻击

#### `POST /attack`

**描述**：执行渗透测试攻击

**请求体**：
```json
{
  "target": "example.com",
  "use_real": true,
  "rule_engine_mode": true
}
```

**响应**：
```json
{
  "target": "example.com",
  "execution_time": "120秒",
  "execution_mode": "real",
  "rule_engine_used": true,
  "rule_engine_model": "rule_engine_v1",
  "attack_chain": [
    {
      "step": 1,
      "tool": "nmap",
      "title": "网络扫描",
      "description": "扫描目标网络的开放端口和服务",
      "duration": "30秒",
      "success": true,
      "severity": "medium",
      "highlight": false
    }
  ],
  "target_analysis": {
    "attack_surface": 0.8,
    "open_ports": 5,
    "vulnerabilities": 3,
    "sql_injections": 1,
    "has_cms": false,
    "cms_type": null,
    "cms_version": null
  },
  "message": "攻击执行完成",
  "timestamp": "2026-04-07T10:00:00Z",
  "success": true
}
```

### 2.4 执行工具

#### `POST /tools/execute`

**描述**：执行单个工具

**请求体**：
```json
{
  "tool": "nmap",
  "target": "example.com",
  "parameters": {
    "ports": "1-1000",
    "flags": "-sV"
  }
}
```

**响应**：
```json
{
  "success": true,
  "output": "Nmap scan report for example.com (93.184.216.34)\nHost is up (0.12s latency).\nPORT    STATE SERVICE  VERSION\n80/tcp  open  http     Apache httpd 2.4.41\n443/tcp open  ssl/http Apache httpd 2.4.41",
  "error": null
}
```

## 3. 漏洞管理 API

### 3.1 验证漏洞

#### `POST /api/v1/vulnerability/validate`

**描述**：验证漏洞的存在性

**请求体**：
```json
{
  "vulnerability": {
    "type": "sql_injection",
    "name": "SQL注入漏洞",
    "severity": "high",
    "url": "http://example.com/login",
    "parameter": "id"
  },
  "target": "example.com"
}
```

**响应**：
```json
{
  "vulnerability": {
    "type": "sql_injection",
    "name": "SQL注入漏洞",
    "severity": "high",
    "url": "http://example.com/login",
    "parameter": "id"
  },
  "validated": true,
  "details": {
    "tool": "sqlmap",
    "output": "SQL injection vulnerability found"
  },
  "poc": {
    "type": "sql_injection",
    "name": "SQL注入漏洞",
    "description": "SQL注入漏洞PoC",
    "payload": "http://example.com/login?id=1' OR '1'='1",
    "steps": [
      "访问: http://example.com/login?id=1' OR '1'='1",
      "查看是否返回所有记录"
    ],
    "expected_result": "返回所有记录，说明存在SQL注入漏洞"
  },
  "timestamp": "2026-04-07T10:00:00Z"
}
```

### 3.2 分析攻击路径

#### `POST /api/v1/attack-path/analyze`

**描述**：分析攻击路径

**请求体**：
```json
{
  "vulnerabilities": [
    {
      "type": "open_port",
      "name": "开放端口",
      "severity": "medium",
      "port": 80
    },
    {
      "type": "sql_injection",
      "name": "SQL注入漏洞",
      "severity": "high",
      "url": "http://example.com/login",
      "parameter": "id"
    }
  ]
}
```

**响应**：
```json
{
  "attack_paths": [
    {
      "path": [
        {
          "type": "open_port",
          "name": "开放端口",
          "severity": "medium",
          "port": 80
        },
        {
          "type": "sql_injection",
          "name": "SQL注入漏洞",
          "severity": "high",
          "url": "http://example.com/login",
          "parameter": "id"
        }
      ],
      "description": "开放端口 80 -> Web漏洞 SQL注入漏洞",
      "risk_score": 6.6
    }
  ],
  "total_paths": 1,
  "highest_risk_path": {
    "path": [
      {
        "type": "open_port",
        "name": "开放端口",
        "severity": "medium",
        "port": 80
      },
      {
        "type": "sql_injection",
        "name": "SQL注入漏洞",
        "severity": "high",
        "url": "http://example.com/login",
        "parameter": "id"
      }
    ],
    "description": "开放端口 80 -> Web漏洞 SQL注入漏洞",
    "risk_score": 6.6
  },
  "summary": "发现 1 条攻击路径，最高风险分数为 6.6"
}
```

### 3.3 评估风险

#### `POST /api/v1/risk/assess`

**描述**：评估漏洞风险

**请求体**：
```json
{
  "vulnerability": {
    "type": "sql_injection",
    "name": "SQL注入漏洞",
    "severity": "high",
    "url": "http://example.com/login",
    "parameter": "id"
  }
}
```

**响应**：
```json
{
  "vulnerability": {
    "type": "sql_injection",
    "name": "SQL注入漏洞",
    "severity": "high",
    "url": "http://example.com/login",
    "parameter": "id"
  },
  "cvss_score": 8.9,
  "impact": "high",
  "likelihood": "medium",
  "risk_level": "high",
  "recommendations": [
    "使用参数化查询",
    "实施输入验证",
    "使用ORM框架",
    "立即修复此漏洞"
  ]
}
```

### 3.4 检查合规性

#### `POST /api/v1/compliance/check`

**描述**：检查目标系统的合规性

**请求体**：
```json
{
  "vulnerabilities": [
    {
      "type": "sql_injection",
      "name": "SQL注入漏洞",
      "severity": "high",
      "url": "http://example.com/login",
      "parameter": "id"
    }
  ],
  "standard": "owasp"
}
```

**响应**：
```json
{
  "standard": "owasp",
  "compliant": false,
  "issues": [
    "A3: Injection - SQL注入漏洞"
  ],
  "recommendations": [
    "实施参数化查询和输入验证"
  ],
  "summary": "发现 1 个OWASP合规问题"
}
```

## 4. 工具管理 API

### 4.1 添加自定义工具

#### `POST /api/v1/tools/custom`

**描述**：添加自定义工具

**请求体**：
```json
{
  "name": "custom_tool",
  "path": "/path/to/tool",
  "description": "自定义工具",
  "category": "web_scanner",
  "params": [
    {
      "name": "target",
      "type": "string",
      "description": "目标地址",
      "required": true
    }
  ]
}
```

**响应**：
```json
{
  "success": true,
  "message": "自定义工具 custom_tool 添加成功"
}
```

### 4.2 执行工具链

#### `POST /api/v1/tools/chain`

**描述**：执行工具链

**请求体**：
```json
{
  "tool_chain": [
    {
      "tool": "nmap",
      "params": {
        "target": "example.com",
        "ports": "1-1000"
      },
      "timeout": 300,
      "stop_on_error": true
    },
    {
      "tool": "nikto",
      "params": {
        "target": "http://example.com"
      },
      "timeout": 300,
      "stop_on_error": true
    }
  ],
  "max_workers": 5,
  "overall_timeout": 600
}
```

**响应**：
```json
{
  "tool_chain": [
    {
      "tool": "nmap",
      "params": {
        "target": "example.com",
        "ports": "1-1000"
      },
      "timeout": 300,
      "stop_on_error": true
    },
    {
      "tool": "nikto",
      "params": {
        "target": "http://example.com"
      },
      "timeout": 300,
      "stop_on_error": true
    }
  ],
  "results": {
    "nmap": "Nmap scan report for example.com (93.184.216.34)\nHost is up (0.12s latency).\nPORT    STATE SERVICE  VERSION\n80/tcp  open  http     Apache httpd 2.4.41\n443/tcp open  ssl/http Apache httpd 2.4.41",
    "nikto": "- Nikto v2.1.6\n---------------------------------------------------------------------------\n+ Target: http://example.com/\n+ Server: Apache/2.4.41 (Ubuntu)"
  },
  "status": "completed"
}
```

## 5. 知识图谱 API

### 5.1 获取图谱数据

#### `GET /api/v1/knowledge-graph/graph`

**描述**：获取完整的知识图谱数据

**响应**：
```json
{
  "success": true,
  "data": {
    "nodes": [
      {
        "id": "target-1",
        "label": "目标服务器",
        "type": "server",
        "properties": {
          "ip": "192.168.1.100",
          "os": "Linux",
          "status": "在线"
        },
        "position": {
          "x": 300,
          "y": 200
        },
        "color": "#3b82f6"
      }
    ],
    "edges": []
  },
  "metadata": {
    "node_count": 1,
    "edge_count": 0,
    "timestamp": "2026-04-07T10:00:00Z"
  }
}
```

### 5.2 导入模拟数据

#### `POST /api/v1/knowledge-graph/import/mock`

**描述**：导入模拟数据到知识图谱

**响应**：
```json
{
  "success": true,
  "message": "模拟数据导入成功",
  "stats": {
    "imported_nodes": 10,
    "imported_edges": 15
  }
}
```

## 6. 认证 API

### 6.1 用户注册

#### `POST /api/v1/auth/register`

**描述**：注册新用户

**请求体**：
```json
{
  "username": "user",
  "email": "user@example.com",
  "password": "password123",
  "full_name": "测试用户"
}
```

**响应**：
```json
{
  "id": 1,
  "username": "user",
  "email": "user@example.com",
  "full_name": "测试用户",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false,
  "created_at": "2026-04-07T10:00:00Z"
}
```

### 6.2 用户登录

#### `POST /api/v1/auth/login`

**描述**：用户登录

**请求体**：
```json
{
  "username": "user",
  "password": "password123"
}
```

**响应**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "user",
    "email": "user@example.com",
    "full_name": "测试用户"
  }
}
```

## 7. 项目管理 API

### 7.1 创建项目

#### `POST /api/v1/projects`

**描述**：创建新的渗透测试项目

**请求体**：
```json
{
  "name": "测试项目",
  "description": "测试项目描述",
  "targets": [
    {
      "target": "example.com",
      "type": "domain"
    }
  ]
}
```

**响应**：
```json
{
  "id": 1,
  "name": "测试项目",
  "description": "测试项目描述",
  "owner_id": 1,
  "status": "active",
  "visibility": "private",
  "created_at": "2026-04-07T10:00:00Z",
  "updated_at": "2026-04-07T10:00:00Z",
  "targets": [
    {
      "target": "example.com",
      "type": "domain"
    }
  ]
}
```

### 7.2 获取项目列表

#### `GET /api/v1/projects`

**描述**：获取用户的项目列表

**响应**：
```json
{
  "projects": [
    {
      "id": 1,
      "name": "测试项目",
      "description": "测试项目描述",
      "owner_id": 1,
      "status": "active",
      "visibility": "private",
      "created_at": "2026-04-07T10:00:00Z",
      "updated_at": "2026-04-07T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

## 8. 报告管理 API

### 8.1 生成报告

#### `POST /api/v1/reports`

**描述**：生成测试报告

**请求体**：
```json
{
  "scan_id": 1,
  "format": "html",
  "title": "测试报告"
}
```

**响应**：
```json
{
  "id": 1,
  "title": "测试报告",
  "scan_id": 1,
  "created_by": 1,
  "format": "html",
  "status": "completed",
  "created_at": "2026-04-07T10:00:00Z",
  "updated_at": "2026-04-07T10:00:00Z"
}
```

### 8.2 获取报告

#### `GET /api/v1/reports/{id}`

**描述**：获取报告详情

**响应**：
```json
{
  "id": 1,
  "title": "测试报告",
  "scan_id": 1,
  "created_by": 1,
  "format": "html",
  "status": "completed",
  "content": "<html><body><h1>测试报告</h1>...</body></html>",
  "created_at": "2026-04-07T10:00:00Z",
  "updated_at": "2026-04-07T10:00:00Z"
}
```

## 9. 监控 API

### 9.1 获取系统 metrics

#### `GET /metrics`

**描述**：获取系统监控指标（Prometheus格式）

**响应**：
```
# HELP clawai_tool_executions_total Total number of tool executions
# TYPE clawai_tool_executions_total counter
clawai_tool_executions_total{tool="nmap"} 10
clawai_tool_executions_total{tool="sqlmap"} 5

# HELP clawai_vulnerabilities_found Total number of vulnerabilities found
# TYPE clawai_vulnerabilities_found counter
clawai_vulnerabilities_found{severity="high"} 3
clawai_vulnerabilities_found{severity="medium"} 5
clawai_vulnerabilities_found{severity="low"} 10
```

### 9.2 实时监控

#### `GET /api/v1/monitor/stats`

**描述**：获取实时监控统计信息

**响应**：
```json
{
  "system": {
    "cpu_usage": 45.5,
    "memory_usage": 60.2,
    "disk_usage": 30.1
  },
  "tools": {
    "total_tools": 29,
    "active_tools": 5,
    "tool_execution_queue": 0
  },
  "scans": {
    "total_scans": 10,
    "active_scans": 2,
    "completed_scans": 8
  }
}
```

## 10. 错误处理

### 10.1 错误响应格式

```json
{
  "detail": "错误信息"
}
```

### 10.2 常见错误码

| 状态码 | 描述 | 示例 |
|--------|------|------|
| 400 | 请求参数错误 | `{"detail": "必须提供目标地址"}` |
| 401 | 未授权 | `{"detail": "未提供认证令牌"}` |
| 403 | 禁止访问 | `{"detail": "权限不足"}` |
| 404 | 资源不存在 | `{"detail": "工具不存在"}` |
| 500 | 内部服务器错误 | `{"detail": "执行工具时出错"}` |
| 503 | 服务不可用 | `{"detail": "工具管理器未初始化"}` |

## 11. 认证与授权

### 11.1 JWT 认证

系统使用 JWT（JSON Web Token）进行认证。在请求需要认证的 API 时，需要在请求头中添加 `Authorization` 字段：

```
Authorization: Bearer <token>
```

### 11.2 基于角色的访问控制 (RBAC)

系统支持基于角色的访问控制，主要角色包括：

- **admin**：管理员角色，拥有所有权限
- **user**：普通用户角色，拥有基本的工具执行和攻击执行权限

### 11.3 权限列表

| 权限名称 | 描述 |
|----------|------|
| TOOL_EXECUTE | 执行工具的权限 |
| ATTACK_EXECUTE | 执行攻击的权限 |
| USER_MANAGE | 管理用户的权限 |
| PROJECT_MANAGE | 管理项目的权限 |
| REPORT_MANAGE | 管理报告的权限 |

## 12. 速率限制

系统对 API 请求实施速率限制，以防止滥用：

- **未认证请求**：每分钟 60 个请求
- **认证请求**：每分钟 300 个请求
- **工具执行**：每分钟 10 个请求
- **攻击执行**：每分钟 5 个请求

## 13. 最佳实践

### 13.1 API 调用最佳实践

1. **使用 HTTPS**：在生产环境中，始终使用 HTTPS 保护 API 通信
2. **使用认证**：对于敏感操作，始终使用 JWT 认证
3. **合理设置超时**：为 API 请求设置合理的超时时间
4. **处理错误**：正确处理 API 返回的错误信息
5. **使用批量操作**：对于多个相关操作，使用批量 API 减少请求次数

### 13.2 性能优化

1. **缓存结果**：对于频繁访问的数据，使用缓存减少 API 调用
2. **分页查询**：对于大量数据，使用分页查询减少数据传输
3. **异步操作**：对于长时间运行的操作，使用异步 API
4. **合理使用工具链**：将相关工具组合成工具链，减少 API 调用次数

## 14. 版本控制

### 14.1 API 版本

当前 API 版本为 v1，通过 URL 路径 `/api/v1/` 访问。未来的 API 版本将通过更新路径中的版本号来区分。

### 14.2 向后兼容性

系统会尽力保持 API 的向后兼容性，但在重大更新时可能会引入 breaking changes。建议开发者在集成时关注版本变化。

## 15. 联系方式

- 项目地址：https://github.com/ClawAI/ClawAI
- 联系邮箱：contact@clawai.com
- 技术支持：support@clawai.com
- API 文档：http://localhost:8000/docs

---

**文档版本**: 2.0.0  
**最后更新**: 2026-04-07  
**维护团队**: ClawAI Development Team