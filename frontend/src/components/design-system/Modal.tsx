import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { Button } from './Button';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  showCloseButton?: boolean;
  closeOnOverlayClick?: boolean;
  closeOnEsc?: boolean;
  footer?: React.ReactNode;
  className?: string;
}

const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEsc = true,
  footer,
  className = '',
}) => {
  const modalRef = useRef<HTMLDivElement>(null);

  // ESC键关闭
  useEffect(() => {
    const handleEsc = (event: KeyboardEvent) => {
      if (closeOnEsc && event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose, closeOnEsc]);

  // 阻止滚动
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  // 点击遮罩层关闭
  const handleOverlayClick = (e: React.MouseEvent) => {
    if (closeOnOverlayClick && e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  // 尺寸类
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    full: 'max-w-full mx-4',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* 遮罩层 */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleOverlayClick}
        aria-hidden="true"
      />

      {/* 模态框容器 */}
      <div className="flex min-h-screen items-center justify-center p-4">
        <div
          ref={modalRef}
          className={`
            relative w-full transform overflow-hidden rounded-lg bg-white dark:bg-gray-800
            shadow-xl transition-all
            ${sizeClasses[size]}
            ${className}
          `}
          role="dialog"
          aria-modal="true"
          aria-labelledby={title ? 'modal-title' : undefined}
        >
          {/* 头部 */}
          {(title || showCloseButton) && (
            <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-6 py-4">
              {title && (
                <h3
                  id="modal-title"
                  className="text-lg font-semibold text-gray-900 dark:text-white"
                >
                  {title}
                </h3>
              )}
              
              {showCloseButton && (
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-md text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  aria-label="关闭"
                >
                  <X className="h-5 w-5" />
                </button>
              )}
            </div>
          )}

          {/* 内容 */}
          <div className="px-6 py-4">
            {children}
          </div>

          {/* 页脚 */}
          {footer && (
            <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// 模态框页脚组件
export interface ModalFooterProps {
  children: React.ReactNode;
  align?: 'left' | 'center' | 'right' | 'between';
  className?: string;
}

export const ModalFooter: React.FC<ModalFooterProps> = ({
  children,
  align = 'right',
  className = '',
}) => {
  const alignClasses = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
    between: 'justify-between',
  };

  return (
    <div className={`flex items-center gap-3 ${alignClasses[align]} ${className}`}>
      {children}
    </div>
  );
};

// 确认模态框
export interface ConfirmModalProps extends Omit<ModalProps, 'children' | 'footer'> {
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel?: () => void;
  variant?: 'danger' | 'warning' | 'info' | 'success';
  isLoading?: boolean;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  message,
  confirmText = '确认',
  cancelText = '取消',
  onConfirm,
  onCancel,
  variant = 'info',
  isLoading = false,
  ...modalProps
}) => {
  const variantConfig = {
    danger: {
      icon: '⚠️',
      confirmVariant: 'error' as const,
    },
    warning: {
      icon: '⚠️',
      confirmVariant: 'warning' as const,
    },
    info: {
      icon: 'ℹ️',
      confirmVariant: 'primary' as const,
    },
    success: {
      icon: '✅',
      confirmVariant: 'success' as const,
    },
  };

  const config = variantConfig[variant];

  const handleCancel = () => {
    onCancel?.();
    modalProps.onClose();
  };

  const handleConfirm = () => {
    onConfirm();
    if (!isLoading) {
      modalProps.onClose();
    }
  };

  return (
    <Modal
      {...modalProps}
      footer={
        <ModalFooter>
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={isLoading}
          >
            {cancelText}
          </Button>
          <Button
            variant={config.confirmVariant}
            onClick={handleConfirm}
            loading={isLoading}
          >
            {confirmText}
          </Button>
        </ModalFooter>
      }
    >
      <div className="text-center">
        <div className="text-4xl mb-4">{config.icon}</div>
        <p className="text-gray-700 dark:text-gray-300">{message}</p>
      </div>
    </Modal>
  );
};

export default Modal;