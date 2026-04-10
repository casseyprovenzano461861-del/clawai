# ClawAI 前后端集成分析 (2026-04-10)

## 核心现状总结

### ✅ 已完成
- WebSocket 框架 (`/ws/per-events`, `/ws/monitoring`) 
- EventBus 事件系统 (5种事件类型: STATE_CHANGED/MESSAGE/TOOL/FINDING/FLAG_FOUND/PROGRESS)
- EventBus → WebSocket 桥接 (attach_eventbus 机制)
- CLI 扫描逻辑完整 (_execute_scan @line644)
- 前端组件框架 (Dashboard/PERPanel/ScanContext)

### ❌ 关键缺失
1. REST API `/api/v1/scan/` 端点（仅有 `/api/v1/pentest/` 流式 API）
2. 扫描引擎独立实现（仅在 CLI chat_cli.py 中）
3. 前端 WebSocket 实际连接逻辑
4. scanService.js 中的 connectScan 具体实现

---

## 1. 前端目录结构（简化）

```
Dashboard.jsx          主仪表板 (1/3 统计卡 + 2/3 tabs)
├─ PERPanel.tsx       P-E-R 实时显示 (EventBus 驱动)
├─ ScanHistory.jsx    历史列表
└─ ValidationResults.jsx 验证结果

context/
  └─ ScanContext.jsx   全局扫描状态 (lastScan/scanHistory/status)

services/
  ├─ apiClient.js      axios 客户端 (base: /api/v1)
  ├─ attackService.js  POST /attack (参考实现)
  └─ scanService.js    (需创建) WebSocket 扫描

hooks/
  ├─ usePERAgent.tsx   WebSocket 事件监听 (需完善)
  └─ useApi.js
```

---

## 2. 后端 REST API 现状

### main.py 直接定义
```
POST /attack                          执行攻击（同步）
POST /tools/execute                   执行单工具
POST /api/v1/tools/chain              执行工具链
POST /api/v1/vulnerability/validate   验证漏洞
```

### 动态加载
```
/api/v1/pentest/start    启动测试（异步）
/api/v1/pentest/stream   流式结果（SSE）
/api/v1/pentest/status   任务状态

/ws/per-events           WebSocket P-E-R 事件 ✅
/ws/monitoring           WebSocket 监控事件 ✅
```

### ❌ 缺失
```
POST /api/v1/scan/start          启动扫描
GET  /api/v1/scan/{scan_id}/status
POST /api/v1/scan/{scan_id}/cancel
或
POST /ws/scan-events             WebSocket 扫描事件
```

---

## 3. CLI 扫描逻辑 (_execute_scan @644行)

### 核心流程
```
FOR i in range(max_iterations):
  1. Planning  → agent.planner() → extract_command()
  2. Executing → agent.execute_command() → tool output
  3. Reflecting → agent.summarizer()
  4. Detection → _parse_finding() / _detect_flags()
  5. Progress → progress.advance()
```

### EventBus 事件发射示例
```python
self._emit_event("STATE_CHANGED", {"state": "scanning"})
self._emit_event("PROGRESS", {"iteration": i+1, "phase": "planning"})
self._emit_tool_event("start", tool_name, {"command": cmd})
self._emit_tool_event("complete", tool_name, {"output": "..."})
self._emit_event("FINDING", {"title": "XSS", "severity": "high"})
```

### 关键参数
- SCAN_PROFILES: quick(3轮)/standard(5轮)/deep(10轮)
- Cookie 自动登录: _auto_login_dvwa() / _auto_login_pikachu()
- Flag 检测: _detect_flags() → 若发现即停止
- 技能直接执行: vuln_hint → registry.execute(skill_id, {target, cookie})

---

## 4. WebSocket & EventBus 架构

### 文件: websocket.py @65-146行

```python
def attach_eventbus(loop):
    """订阅 5 种事件，序列化后广播到 WebSocket"""
    
    # 事件序列化示例
    def _serialize_tool(event):
        return {
            "type": "tool_event",
            "status": "start|complete",
            "name": tool_name,
            "args": {...},
            "result": {...},
            "timestamp": ISO8601
        }
    
    bus.subscribe(EventType.STATE_CHANGED, handler)
    bus.subscribe(EventType.MESSAGE, handler)
    bus.subscribe(EventType.TOOL, handler)
    bus.subscribe(EventType.FINDING, handler)
    bus.subscribe(EventType.PROGRESS, handler)
```

### 事件流向
```
CLI._emit_event()
  ↓
EventBus.emit(Event)
  ↓
订阅者列表：
├─ CLI 内部回调 (on_message/on_tool_execution)
├─ WebSocket 桥接
│  └─ serialize → broadcast() → 所有客户端
└─ 其他订阅者
```

---

## 5. 集成需要做的事情

### 后端 (优先级: HIGH)

1. **创建扫描引擎** src/shared/backend/core/scan_engine.py
   ```python
   async def execute_scan_with_events(
       target, profile="standard",
       emit_event_fn=None  # 事件回调
   ) -> Dict
   ```
   - 参数化 EventBus 回调
   - 复用 CLI 逻辑（规划-执行-反思）
   - 支持 skills 覆盖

2. **创建 REST 端点** src/shared/backend/api/v1/scan.py
   ```python
   POST /api/v1/scan/start
       {target, profile, skills?, mode?}
       → {scan_id, status}
   
   GET /api/v1/scan/{scan_id}/status
       → {status, progress, findings_count}
   
   POST /api/v1/scan/{scan_id}/cancel
   ```

3. **增强 WebSocket** (或新建 /ws/scan-events)
   - 支持 action: "start_scan" | "cancel_scan" | "ping"
   - 推送 type: "scan_started|progress|tool|finding|error"

4. **初始化 Skills Registry**（在 main.py lifespan）
   ```python
   skill_registry = get_skill_registry()
   ```

### 前端 (优先级: HIGH)

1. **创建 scanService.js**
   ```javascript
   scanService.connectScan(target, profile, {
     onProgress: (percent, desc) => {},
     onToolEvent: (event) => {},
     onFinding: (finding) => {},
     onComplete: (result) => {},
     onError: (error) => {}
   })
   ```

2. **增强 ScanContext**
   - Reducer 支持 SCAN_PROGRESS/TOOL_EVENT/ADD_FINDING
   - startScanWithWebSocket() 方法
   - 历史记录持久化

3. **更新 Dashboard**
   ```jsx
   <CyberInput placeholder="输入目标" />
   <select>快速|标准|深度</select>
   <button onClick={startScanWithWebSocket}>开始扫描</button>
   
   {scanStatus === 'scanning' && <PERPanel />}
   {scanStatus === 'done' && <ValidationResults result={lastScan} />}
   ```

4. **增强 PERPanel.tsx**
   - 连接 ScanContext
   - 显示工具执行时间线
   - 进度条实时更新
   - 发现实时追加

---

## 6. 实施路线

### 阶段 1: 后端扫描引擎（5-10小时）
- ✅ 抽取 `_execute_scan()` 核心逻辑
- ✅ 参数化 EventBus emit_event_fn
- ✅ 测试独立执行（不依赖 CLI）

### 阶段 2: 后端 API（3-5小时）
- ✅ 创建 `/api/v1/scan/start`
- ✅ 创建 `/api/v1/scan/{id}/status`
- ✅ 可选：`/ws/scan-events` WebSocket 支持

### 阶段 3: 前端集成（10-15小时）
- ✅ scanService.js + WebSocket 连接
- ✅ ScanContext 增强
- ✅ Dashboard 表单联动
- ✅ PERPanel 事件监听

### 阶段 4: 测试与调试（5-10小时）
- ✅ 端到端测试
- ✅ 错误处理、网络恢复
- ✅ 性能优化

总计：**25-40 小时**

---

## 7. 关键文件位置

| 功能 | 文件 | 行数 |
|------|------|------|
| CLI 扫描核心 | src/cli/chat_cli.py | _execute_scan @644 |
| WebSocket 桥接 | src/shared/backend/api/websocket.py | attach_eventbus @65 |
| EventBus 定义 | src/shared/backend/events.py | EventType / emit() |
| 后端初始化 | src/shared/backend/main.py | lifespan @77 |
| 前端主页 | frontend/src/pages/Dashboard.jsx | ~400 行 |
| 上下文 | frontend/src/context/ScanContext.jsx | ~200 行 |

---

## 8. 关键集成点

1. **EventBus 作为中枢**
   - CLI emit_event() → EventBus.emit()
   - 后端扫描引擎 emit_event_fn() → EventBus.emit()
   - WebSocket 桥接订阅所有事件

2. **Skills Registry 共享**
   - 在 main.py 启动时初始化一次
   - API 和 CLI 都使用同一实例

3. **WebSocket 事件流**
   - 后端 emit → EventBus → WebSocket 广播
   - 前端 WebSocket 接收 → 更新 ScanContext
   - React 重新渲染 (Dashboard/PERPanel)

---

**分析完成日期**: 2026-04-10
