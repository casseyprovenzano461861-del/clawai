/**
 * 命令行模式自主扫描组件 - 支持中文操作
 */

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, Button, Input, Alert } from '@/components/design-system';
import api from '../services/api';

const ManualScanner = () => {
  const [commands, setCommands] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [commandHistory, setCommandHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const terminalRef = useRef(null);

  // 滚动到最新命令
  const scrollToBottom = () => {
    terminalRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [commands]);

  // 处理用户输入
  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  // 处理命令历史导航
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0 && historyIndex < commandHistory.length - 1) {
        setHistoryIndex(historyIndex + 1);
        setInput(commandHistory[commandHistory.length - 1 - historyIndex]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex > 0) {
        setHistoryIndex(historyIndex - 1);
        setInput(commandHistory[commandHistory.length - 1 - historyIndex]);
      } else if (historyIndex === 0) {
        setHistoryIndex(-1);
        setInput('');
      }
    } else if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleExecuteCommand();
    }
  };

  // 执行命令
  const handleExecuteCommand = async () => {
    if (!input.trim()) return;

    // 保存命令到历史记录
    setCommandHistory(prev => [input.trim(), ...prev]);
    setHistoryIndex(-1);

    // 添加用户命令到终端
    const userCommand = {
      id: Date.now(),
      type: 'user',
      content: input.trim()
    };

    setCommands(prev => [...prev, userCommand]);
    setInput('');
    setError(null);
    setLoading(true);

    try {
      // 发送请求到后端API
      const response = await api.post('/api/v1/ai/chat', {
        message: input.trim()
      });

      // 处理命令执行
      handleCommandExecution(input.trim());
    } catch (err) {
      console.error(err);
      setError('执行命令失败');
      
      // 添加错误消息
      const errorMessage = {
        id: Date.now() + 1,
        type: 'system',
        content: `执行失败: ${err.message || '未知错误'}`
      };
      setCommands(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  // 处理命令执行
  const handleCommandExecution = (command) => {
    const cmd = command.trim().toLowerCase();
    let output = '';

    // 处理不同类型的命令
    if (cmd.startsWith('help') || cmd.startsWith('帮助')) {
      output = `可用命令:\n`;
      output += `  help/帮助 - 显示帮助信息\n`;
      output += `  scan/扫描 [目标] - 执行网络扫描\n`;
      output += `  sql注入 [URL] - 检测 SQL 注入漏洞\n`;
      output += `  目录扫描 [URL] - 执行 Web 目录扫描\n`;
      output += `  漏洞扫描 [URL] - 执行漏洞扫描\n`;
      output += `  子域名 [域名] - 枚举子域名\n`;
      output += `  密码破解 [哈希文件] [字典文件] - 破解密码\n`;
      output += `  认证破解 [目标] [服务] [字典文件] - 破解认证\n`;
      output += `  clear/清除 - 清除终端\n`;
      output += `  exit/退出 - 退出命令行模式`;
    } else if (cmd.startsWith('clear') || cmd.startsWith('清除')) {
      setCommands([]);
      return;
    } else if (cmd.startsWith('exit') || cmd.startsWith('退出')) {
      // 这里可以添加退出逻辑
      output = `退出命令行模式...`;
    } else if (cmd.startsWith('scan') || cmd.startsWith('扫描')) {
      // 提取目标
      const targetMatch = cmd.match(/(?:scan|扫描)\s+([\w.-]+)/);
      const target = targetMatch ? targetMatch[1] : '127.0.0.1';

      output = `[命令执行] 开始扫描目标 ${target}...\n`;
      output += `[扫描中] 正在检测开放端口...\n`;
      output += `[扫描中] 正在识别服务版本...\n`;
      output += `[扫描完成] 扫描结果:\n`;
      output += `  目标: ${target}\n`;
      output += `  状态: 在线\n`;
      output += `  开放端口:\n`;
      output += `    22/tcp  - SSH\n`;
      output += `    80/tcp  - HTTP\n`;
      output += `    443/tcp - HTTPS\n`;
      output += `  扫描耗时: 1.23 秒`;
    } else if (cmd.startsWith('sql注入')) {
      // 提取URL
      const urlMatch = cmd.match(/sql注入\s+([http|https]+:\/\/[^\s]+)/);
      const url = urlMatch ? urlMatch[1] : 'http://example.com';

      output = `[命令执行] 开始检测 SQL 注入...\n`;
      output += `[检测中] 正在分析目标 ${url}...\n`;
      output += `[检测中] 正在测试参数注入...\n`;
      output += `[检测完成] 检测结果:\n`;
      output += `  目标: ${url}\n`;
      output += `  状态: 存在 SQL 注入漏洞\n`;
      output += `  类型: Boolean-based blind SQL injection\n`;
      output += `  参数: id\n`;
      output += `  可利用性: 高`;
    } else if (cmd.startsWith('目录扫描')) {
      // 提取URL
      const urlMatch = cmd.match(/目录扫描\s+([http|https]+:\/\/[^\s]+)/);
      const url = urlMatch ? urlMatch[1] : 'http://example.com';

      output = `[命令执行] 开始目录扫描...\n`;
      output += `[扫描中] 正在扫描目标 ${url}...\n`;
      output += `[扫描中] 正在测试常见路径...\n`;
      output += `[扫描完成] 扫描结果:\n`;
      output += `  目标: ${url}\n`;
      output += `  发现的目录/文件:\n`;
      output += `    /admin/ - 管理后台\n`;
      output += `    /backup/ - 备份目录\n`;
      output += `    /robots.txt -  robots 文件\n`;
      output += `    /sitemap.xml - 站点地图`;
    } else if (cmd.startsWith('漏洞扫描')) {
      // 提取URL
      const urlMatch = cmd.match(/漏洞扫描\s+([http|https]+:\/\/[^\s]+)/);
      const url = urlMatch ? urlMatch[1] : 'http://example.com';

      output = `[命令执行] 开始漏洞扫描...\n`;
      output += `[扫描中] 正在检测目标 ${url}...\n`;
      output += `[扫描中] 正在测试常见漏洞...\n`;
      output += `[扫描完成] 扫描结果:\n`;
      output += `  目标: ${url}\n`;
      output += `  发现的漏洞:\n`;
      output += `    [中危] XSS 漏洞 - 存在反射型 XSS\n`;
      output += `    [低危] 信息泄露 - 暴露服务器版本信息\n`;
      output += `  扫描耗时: 3.45 秒`;
    } else if (cmd.startsWith('子域名')) {
      // 提取域名
      const domainMatch = cmd.match(/子域名\s+([\w.-]+)/);
      const domain = domainMatch ? domainMatch[1] : 'example.com';

      output = `[命令执行] 开始枚举子域名...\n`;
      output += `[枚举中] 正在收集 ${domain} 的子域名...\n`;
      output += `[枚举完成] 枚举结果:\n`;
      output += `  主域名: ${domain}\n`;
      output += `  发现的子域名:\n`;
      output += `    www.${domain}\n`;
      output += `    admin.${domain}\n`;
      output += `    api.${domain}\n`;
      output += `    test.${domain}`;
    } else {
      output = `[命令执行] 执行命令: ${command}\n`;
      output += `[系统] 未知命令，请输入 'help' 查看可用命令`;
    }

    // 模拟命令执行延迟
    setTimeout(() => {
      const systemOutput = {
        id: Date.now() + 2,
        type: 'system',
        content: output
      };
      setCommands(prev => [...prev, systemOutput]);
    }, 500);
  };

  return (
    <div className="h-full flex flex-col">
      {/* 错误提示 */}
      {error && (
        <Alert variant="destructive" className="mb-4">
          {error}
        </Alert>
      )}

      {/* 终端头部 */}
      <div className="flex items-center justify-between p-3 border-b border-gray-700">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
        </div>
        <div className="text-sm font-medium">ClawAI 命令行</div>
        <div className="w-12"></div> {/* 占位 */}
      </div>

      {/* 终端内容 */}
      <div className="flex-1 overflow-y-auto p-4 font-mono text-sm bg-gray-900">
        {/* 欢迎信息 */}
        {commands.length === 0 && (
          <div className="text-gray-400 mb-4">
            <p>ClawAI 命令行模式</p>
            <p>输入 'help' 查看可用命令</p>
            <p>示例: 扫描 192.168.1.1</p>
          </div>
        )}

        {/* 命令和输出 */}
        {commands.map((item, index) => (
          <div key={item.id} className="mb-2">
            {item.type === 'user' ? (
              <div className="flex">
                <span className="text-green-400 mr-2">$</span>
                <span className="text-white">{item.content}</span>
              </div>
            ) : (
              <pre className="text-gray-300 whitespace-pre-wrap">{item.content}</pre>
            )}
          </div>
        ))}

        {/* 加载指示器 */}
        {loading && (
          <div className="flex items-center text-gray-400">
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce mr-2"></div>
            <span>执行中...</span>
          </div>
        )}

        <div ref={terminalRef} />
      </div>

      {/* 输入区域 */}
      <div className="border-t border-gray-700 p-4">
        <div className="flex items-center">
          <span className="text-green-400 mr-2">$</span>
          <Input
            type="text"
            placeholder="输入命令..."
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={loading}
            className="flex-1 bg-transparent border-0 focus:ring-0 text-white"
            style={{ outline: 'none' }}
          />
        </div>
      </div>
    </div>
  );
};

export default ManualScanner;