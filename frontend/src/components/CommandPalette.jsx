import React, { useState, useEffect, useRef } from 'react';
import {
  Search, Command, FileText, Settings, Target, Network,
  Activity, History, Download, HelpCircle, Moon, Sun,
  Home, Shield, Zap, User, LogOut
} from 'lucide-react';
import useKeyboardShortcuts from '../hooks/useKeyboardShortcuts';

/**
 * 命令面板组件
 * 类似 VS Code 的命令面板，支持快速搜索和执行命令
 */
const CommandPalette = ({ isOpen, onClose, onNavigate, darkMode = true }) => {
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  // 命令列表
  const commands = [
    {
      id: 'home',
      name: '首页',
      description: '返回仪表板首页',
      icon: Home,
      shortcut: 'G H',
      action: () => onNavigate('/')
    },
    {
      id: 'scan',
      name: '安全扫描',
      description: '开始新的安全扫描',
      icon: Target,
      shortcut: 'G S',
      action: () => onNavigate('/scan')
    },
    {
      id: 'knowledge-graph',
      name: '知识图谱',
      description: '查看知识图谱',
      icon: Network,
      shortcut: 'G K',
      action: () => onNavigate('/knowledge-graph')
    },
    {
      id: 'monitor',
      name: '实时监控',
      description: '打开实时监控面板',
      icon: Activity,
      shortcut: 'G M',
      action: () => onNavigate('/monitor')
    },
    {
      id: 'history',
      name: '扫描历史',
      description: '查看扫描历史记录',
      icon: History,
      shortcut: 'G H',
      action: () => onNavigate('/history')
    },
    {
      id: 'reports',
      name: '报告管理',
      description: '生成和管理安全报告',
      icon: FileText,
      shortcut: 'G R',
      action: () => onNavigate('/reports')
    },
    {
      id: 'plugins',
      name: '插件管理',
      description: '管理插件和扩展',
      icon: Zap,
      shortcut: 'G P',
      action: () => onNavigate('/plugins')
    },
    {
      id: 'settings',
      name: '系统设置',
      description: '配置系统参数',
      icon: Settings,
      shortcut: 'Ctrl+,',
      action: () => onNavigate('/settings')
    },
    {
      id: 'help',
      name: '帮助文档',
      description: '查看帮助和快捷键',
      icon: HelpCircle,
      shortcut: 'F1',
      action: () => onNavigate('/help')
    },
    {
      id: 'theme',
      name: '切换主题',
      description: '切换深色/浅色主题',
      icon: darkMode ? Sun : Moon,
      shortcut: 'Ctrl+T',
      action: () => {
        // 切换主题逻辑（待接入 ThemeContext）
      }
    },
  ];

  // 过滤命令
  const filteredCommands = commands.filter(cmd => {
    if (!search) return true;
    const query = search.toLowerCase();
    return (
      cmd.name.toLowerCase().includes(query) ||
      cmd.description.toLowerCase().includes(query)
    );
  });

  // 聚焦输入框
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      setSearch('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // 滚动到选中项
  useEffect(() => {
    if (listRef.current) {
      const selectedElement = listRef.current.children[selectedIndex];
      if (selectedElement) {
        selectedElement.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [selectedIndex]);

  // 键盘导航
  useKeyboardShortcuts({
    'arrowup': () => {
      setSelectedIndex(i => (i > 0 ? i - 1 : filteredCommands.length - 1));
    },
    'arrowdown': () => {
      setSelectedIndex(i => (i < filteredCommands.length - 1 ? i + 1 : 0));
    },
    'escape': () => {
      onClose();
    },
    'enter': () => {
      if (filteredCommands[selectedIndex]) {
        filteredCommands[selectedIndex].action();
        onClose();
      }
    }
  }, { enabled: isOpen });

  // 执行命令
  const executeCommand = (command) => {
    command.action();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
      {/* 遮罩 */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* 面板 */}
      <div className={`relative w-full max-w-xl mx-4 rounded-xl shadow-2xl overflow-hidden ${
        darkMode ? 'bg-gray-800' : 'bg-white'
      }`}>
        {/* 搜索框 */}
        <div className={`flex items-center px-4 border-b ${
          darkMode ? 'border-gray-700' : 'border-gray-200'
        }`}>
          <Search className="w-5 h-5 opacity-50" />
          <input
            ref={inputRef}
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="搜索命令..."
            className={`flex-1 px-4 py-4 bg-transparent outline-none ${
              darkMode ? 'text-white placeholder-gray-500' : 'text-gray-900 placeholder-gray-400'
            }`}
          />
          <kbd className={`px-2 py-1 rounded text-xs ${
            darkMode ? 'bg-gray-700 text-gray-400' : 'bg-gray-100 text-gray-500'
          }`}>
            ESC
          </kbd>
        </div>

        {/* 命令列表 */}
        <div
          ref={listRef}
          className="max-h-80 overflow-y-auto py-2"
        >
          {filteredCommands.length === 0 ? (
            <div className={`px-4 py-8 text-center ${
              darkMode ? 'text-gray-500' : 'text-gray-400'
            }`}>
              <Command className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>未找到匹配的命令</p>
            </div>
          ) : (
            filteredCommands.map((cmd, index) => {
              const Icon = cmd.icon;
              const isSelected = index === selectedIndex;

              return (
                <div
                  key={cmd.id}
                  onClick={() => executeCommand(cmd)}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={`flex items-center px-4 py-3 cursor-pointer ${
                    isSelected
                      ? darkMode
                        ? 'bg-blue-600/20'
                        : 'bg-blue-50'
                      : darkMode
                        ? 'hover:bg-gray-700/50'
                        : 'hover:bg-gray-50'
                  }`}
                >
                  {/* 图标 */}
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    darkMode ? 'bg-gray-700' : 'bg-gray-100'
                  }`}>
                    <Icon className={`w-4 h-4 ${
                      isSelected ? 'text-blue-500' : 'opacity-70'
                    }`} />
                  </div>

                  {/* 文字 */}
                  <div className="flex-1 ml-3">
                    <div className={`font-medium ${
                      isSelected ? 'text-blue-500' : ''
                    }`}>
                      {cmd.name}
                    </div>
                    <div className={`text-sm ${
                      darkMode ? 'text-gray-500' : 'text-gray-400'
                    }`}>
                      {cmd.description}
                    </div>
                  </div>

                  {/* 快捷键 */}
                  {cmd.shortcut && (
                    <kbd className={`px-2 py-1 rounded text-xs ${
                      darkMode ? 'bg-gray-700 text-gray-400' : 'bg-gray-100 text-gray-500'
                    }`}>
                      {cmd.shortcut}
                    </kbd>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* 底部提示 */}
        <div className={`px-4 py-2 border-t ${
          darkMode ? 'border-gray-700 bg-gray-900/50' : 'border-gray-200 bg-gray-50'
        }`}>
          <div className="flex items-center justify-between text-xs opacity-50">
            <div className="flex items-center space-x-4">
              <span>
                <kbd className="px-1 rounded bg-gray-700/50 mr-1">↑↓</kbd>
                导航
              </span>
              <span>
                <kbd className="px-1 rounded bg-gray-700/50 mr-1">↵</kbd>
                选择
              </span>
              <span>
                <kbd className="px-1 rounded bg-gray-700/50 mr-1">ESC</kbd>
                关闭
              </span>
            </div>
            <span>
              <kbd className="px-1 rounded bg-gray-700/50 mr-1">Ctrl</kbd>
              <kbd className="px-1 rounded bg-gray-700/50 mr-1">K</kbd>
              打开命令面板
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommandPalette;
