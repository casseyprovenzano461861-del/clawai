/**
 * 类名合并工具函数
 * 类似于 clsx 或 classnames 的简化版本
 */

/**
 * 合并类名
 * @param {...any} args - 类名参数，可以是字符串、对象、数组
 * @returns {string} 合并后的类名字符串
 */
export function cn(...args) {
  const classes = [];

  for (const arg of args) {
    if (!arg) continue;

    if (typeof arg === 'string') {
      classes.push(arg);
    } else if (Array.isArray(arg)) {
      const inner = cn(...arg);
      if (inner) classes.push(inner);
    } else if (typeof arg === 'object') {
      for (const key in arg) {
        if (Object.prototype.hasOwnProperty.call(arg, key) && arg[key]) {
          classes.push(key);
        }
      }
    }
  }

  return classes.join(' ');
}

export default cn;
