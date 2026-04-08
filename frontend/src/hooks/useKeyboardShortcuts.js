import { useEffect, useCallback, useRef, useState } from 'react';

/**
 * 键盘快捷键 Hook
 * 
 * @param {Object} shortcuts - 快捷键配置对象
 * @param {Object} options - 配置选项
 * 
 * @example
 * useKeyboardShortcuts({
 *   'ctrl+enter': () => executeScan(),
 *   'escape': () => closeModal(),
 *   'ctrl+k': () => openCommandPalette(),
 * });
 */
const useKeyboardShortcuts = (shortcuts = {}, options = {}) => {
  const {
    enabled = true,
    preventDefault = true,
    stopPropagation = false,
    target = null,
  } = options;

  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  const parseShortcut = useCallback((shortcut) => {
    const parts = shortcut.toLowerCase().split('+');
    const key = parts.pop();
    const modifiers = {
      ctrl: parts.includes('ctrl'),
      alt: parts.includes('alt'),
      shift: parts.includes('shift'),
      meta: parts.includes('meta') || parts.includes('cmd'),
    };
    return { key, modifiers };
  }, []);

  const matchesShortcut = useCallback((event, parsed) => {
    const { key, modifiers } = parsed;

    if (event.key.toLowerCase() !== key) return false;
    if (modifiers.ctrl !== (event.ctrlKey || event.metaKey)) return false;
    if (modifiers.alt !== event.altKey) return false;
    if (modifiers.shift !== event.shiftKey) return false;
    if (modifiers.meta !== event.metaKey) return false;

    return true;
  }, []);

  const handleKeyDown = useCallback((event) => {
    const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName) ||
                    event.target.isContentEditable;

    for (const [shortcut, callback] of Object.entries(shortcutsRef.current)) {
      const parsed = parseShortcut(shortcut);

      if (isInput && !parsed.modifiers.ctrl && !parsed.modifiers.meta) {
        continue;
      }

      if (matchesShortcut(event, parsed)) {
        if (preventDefault) {
          event.preventDefault();
        }
        if (stopPropagation) {
          event.stopPropagation();
        }
        callback(event);
        return;
      }
    }
  }, [parseShortcut, matchesShortcut, preventDefault, stopPropagation]);

  useEffect(() => {
    if (!enabled) return;

    const targetElement = target?.current || document;
    targetElement.addEventListener('keydown', handleKeyDown);

    return () => {
      targetElement.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown, enabled, target]);

  return null;
};

/**
 * 常用快捷键预设
 */
export const COMMON_SHORTCUTS = {
  SAVE: 'ctrl+s',
  UNDO: 'ctrl+z',
  REDO: 'ctrl+shift+z',
  SELECT_ALL: 'ctrl+a',
  COPY: 'ctrl+c',
  PASTE: 'ctrl+v',
  CUT: 'ctrl+x',
  GO_HOME: 'ctrl+home',
  GO_BACK: 'alt+left',
  GO_FORWARD: 'alt+right',
  SEARCH: 'ctrl+f',
  QUICK_SEARCH: 'ctrl+k',
  CLOSE: 'escape',
  CLOSE_TAB: 'ctrl+w',
  REFRESH: 'f5',
  HARD_REFRESH: 'ctrl+f5',
  HELP: 'f1',
  FULLSCREEN: 'f11',
};

/**
 * 命令面板 Hook
 */
export const useCommandPalette = (commands = [], options = {}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  const filteredCommands = commands.filter(cmd =>
    cmd.name.toLowerCase().includes(search.toLowerCase()) ||
    cmd.description?.toLowerCase().includes(search.toLowerCase())
  );

  useKeyboardShortcuts({
    'ctrl+k': () => setIsOpen(true),
    'escape': () => {
      setIsOpen(false);
      setSearch('');
    },
  }, options);

  useEffect(() => {
    setSelectedIndex(0);
  }, [search]);

  const navigateUp = useCallback(() => {
    setSelectedIndex(i => (i > 0 ? i - 1 : filteredCommands.length - 1));
  }, [filteredCommands.length]);

  const navigateDown = useCallback(() => {
    setSelectedIndex(i => (i < filteredCommands.length - 1 ? i + 1 : 0));
  }, [filteredCommands.length]);

  const executeSelected = useCallback(() => {
    const cmd = filteredCommands[selectedIndex];
    if (cmd?.action) {
      cmd.action();
      setIsOpen(false);
      setSearch('');
    }
  }, [filteredCommands, selectedIndex]);

  useKeyboardShortcuts({
    'arrowup': navigateUp,
    'arrowdown': navigateDown,
    'enter': executeSelected,
  }, { enabled: isOpen, target: null });

  return {
    isOpen,
    open: () => setIsOpen(true),
    close: () => {
      setIsOpen(false);
      setSearch('');
    },
    toggle: () => setIsOpen(v => !v),
    search,
    setSearch,
    filteredCommands,
    selectedIndex,
    setSelectedIndex,
    executeSelected,
  };
};

export default useKeyboardShortcuts;
