import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
  icon?: React.ReactNode;
}

export interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'onChange'> {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  fullWidth?: boolean;
  searchable?: boolean;
  multiple?: boolean;
  clearable?: boolean;
}

const Select: React.FC<SelectProps> = ({
  label,
  error,
  helperText,
  options,
  placeholder = '请选择',
  value,
  onChange,
  fullWidth = true,
  searchable = false,
  multiple = false,
  clearable = false,
  disabled,
  className = '',
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedValues, setSelectedValues] = useState<string[]>(
    value ? (multiple ? value.split(',') : [value]) : []
  );
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // 过滤选项
  const filteredOptions = searchable
    ? options.filter(option =>
        option.label.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : options;

  // 获取选中项的标签
  const getSelectedLabel = () => {
    if (multiple) {
      const selectedLabels = selectedValues
        .map(val => options.find(opt => opt.value === val)?.label)
        .filter(Boolean);
      return selectedLabels.length > 0
        ? `${selectedLabels.length} 项已选择`
        : placeholder;
    }
    
    const selectedOption = options.find(opt => opt.value === value);
    return selectedOption?.label || placeholder;
  };

  // 处理选择
  const handleSelect = (optionValue: string) => {
    if (multiple) {
      const newValues = selectedValues.includes(optionValue)
        ? selectedValues.filter(v => v !== optionValue)
        : [...selectedValues, optionValue];
      
      setSelectedValues(newValues);
      onChange?.(newValues.join(','));
    } else {
      onChange?.(optionValue);
      setIsOpen(false);
      setSearchTerm('');
    }
  };

  // 清除选择
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (multiple) {
      setSelectedValues([]);
      onChange?.('');
    } else {
      onChange?.('');
    }
  };

  // 点击外部关闭下拉
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 聚焦搜索输入框
  useEffect(() => {
    if (isOpen && searchable && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen, searchable]);

  // 基础样式
  const baseClasses = 'relative';
  const widthClass = fullWidth ? 'w-full' : '';

  // 选择框样式
  const selectBoxClasses = [
    'flex items-center justify-between px-3 py-2 border rounded-md cursor-pointer',
    'bg-white dark:bg-gray-800',
    'border-gray-300 dark:border-gray-700',
    'hover:border-gray-400 dark:hover:border-gray-600',
    'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
    disabled ? 'opacity-50 cursor-not-allowed' : '',
    error ? 'border-error-500 focus:ring-error-500' : '',
    widthClass,
    className,
  ].filter(Boolean).join(' ');

  // 下拉菜单样式
  const dropdownClasses = [
    'absolute z-50 mt-1 w-full',
    'bg-white dark:bg-gray-800',
    'border border-gray-200 dark:border-gray-700',
    'rounded-md shadow-lg',
    'max-h-60 overflow-auto',
  ].filter(Boolean).join(' ');

  return (
    <div className={`${baseClasses} ${widthClass}`} ref={containerRef}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          {label}
          {props.required && <span className="text-error-500 ml-1">*</span>}
        </label>
      )}

      <div
        className={selectBoxClasses}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        role="combobox"
      >
        <span className="truncate text-gray-700 dark:text-gray-300">
          {getSelectedLabel()}
        </span>
        
        <div className="flex items-center gap-2">
          {clearable && (multiple ? selectedValues.length > 0 : value) && (
            <button
              type="button"
              onClick={handleClear}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              aria-label="清除选择"
            >
              ×
            </button>
          )}
          <ChevronDown
            className={`h-4 w-4 text-gray-400 transition-transform ${
              isOpen ? 'transform rotate-180' : ''
            }`}
          />
        </div>
      </div>

      {isOpen && (
        <div className={dropdownClasses}>
          {searchable && (
            <div className="sticky top-0 bg-white dark:bg-gray-800 p-2 border-b border-gray-200 dark:border-gray-700">
              <input
                ref={searchInputRef}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="搜索..."
                className="w-full px-3 py-1 text-sm border border-gray-300 dark:border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          )}

          <div role="listbox" className="py-1">
            {filteredOptions.length > 0 ? (
              filteredOptions.map((option) => {
                const isSelected = multiple
                  ? selectedValues.includes(option.value)
                  : value === option.value;
                const isDisabled = option.disabled || disabled;

                return (
                  <div
                    key={option.value}
                    role="option"
                    aria-selected={isSelected}
                    aria-disabled={isDisabled}
                    onClick={() => !isDisabled && handleSelect(option.value)}
                    className={`
                      flex items-center justify-between px-3 py-2 cursor-pointer
                      ${isSelected ? 'bg-primary-50 dark:bg-primary-900/20' : ''}
                      ${isDisabled
                        ? 'opacity-50 cursor-not-allowed'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                      }
                    `}
                  >
                    <div className="flex items-center gap-2">
                      {option.icon && (
                        <span className="text-gray-400">{option.icon}</span>
                      )}
                      <span className="text-gray-700 dark:text-gray-300">
                        {option.label}
                      </span>
                    </div>
                    
                    {isSelected && (
                      <Check className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                    )}
                  </div>
                );
              })
            ) : (
              <div className="px-3 py-2 text-gray-500 text-center">
                无匹配选项
              </div>
            )}
          </div>
        </div>
      )}

      {error && (
        <p className="mt-1 text-sm text-error-600">{error}</p>
      )}

      {helperText && !error && (
        <p className="mt-1 text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  );
};

export default Select;