import React from 'react';

/**
 * 快捷键帮助组件
 */
const ShortcutHelp = ({ shortcuts, darkMode = true }) => {
  const formatKey = (key) => {
    const keyMap = {
      'ctrl': 'Ctrl',
      'alt': 'Alt',
      'shift': 'Shift',
      'meta': '⌘',
      'cmd': '⌘',
      'escape': 'Esc',
      'enter': 'Enter',
      'arrowup': '↑',
      'arrowdown': '↓',
      'arrowleft': '←',
      'arrowright': '→',
    };
    return keyMap[key.toLowerCase()] || key.toUpperCase();
  };

  const formatShortcut = (shortcut) => {
    return shortcut.split('+').map(formatKey).join(' + ');
  };

  return (
    <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-4`}>
      <h4 className="font-semibold mb-3">快捷键</h4>
      <div className="space-y-2">
        {Object.entries(shortcuts).map(([key, description]) => (
          <div key={key} className="flex justify-between items-center text-sm">
            <span className="opacity-70">{description}</span>
            <kbd className={`px-2 py-1 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-100'} font-mono text-xs`}>
              {formatShortcut(key)}
            </kbd>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ShortcutHelp;
