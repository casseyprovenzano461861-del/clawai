import React from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

/**
 * 错误边界组件
 * 捕获子组件树中的 JavaScript 错误，显示友好的错误页面
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    };
  }

  static getDerivedStateFromError(error) {
    // 更新 state 使下一次渲染能够显示降级后的 UI
    return { hasError: true, errorId: Date.now() };
  }

  static getDerivedStateFromProps(props, state) {
    // 如果 children 改变，重置错误状态
    if (props.resetKey && props.resetKey !== state.errorId) {
      return { hasError: false, error: null, errorInfo: null };
    }
    return null;
  }

  componentDidCatch(error, errorInfo) {
    // 记录错误信息
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // 可以将错误日志上报给服务器
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // 如果有错误上报函数，调用它
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render() {
    if (this.state.hasError) {
      // 自定义错误页面
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 默认错误页面
      return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
          <div className="max-w-lg w-full">
            {/* 错误卡片 */}
            <div className="bg-gray-800 rounded-2xl shadow-2xl overflow-hidden">
              {/* 头部 */}
              <div className="bg-gradient-to-r from-red-600 to-orange-600 p-6">
                <div className="flex items-center">
                  <AlertTriangle className="w-12 h-12 text-white mr-4" />
                  <div>
                    <h1 className="text-2xl font-bold text-white">
                      出了一些问题
                    </h1>
                    <p className="text-red-100 mt-1">
                      应用遇到了一个错误，但不要担心
                    </p>
                  </div>
                </div>
              </div>

              {/* 内容 */}
              <div className="p-6">
                <p className="text-gray-300 mb-4">
                  这个错误已被记录。你可以尝试以下操作：
                </p>

                {/* 操作按钮 */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
                  <button
                    onClick={this.handleRetry}
                    className="flex items-center justify-center px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    重试
                  </button>
                  <button
                    onClick={this.handleReload}
                    className="flex items-center justify-center px-4 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    刷新页面
                  </button>
                  <button
                    onClick={this.handleGoHome}
                    className="flex items-center justify-center px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                  >
                    <Home className="w-4 h-4 mr-2" />
                    返回首页
                  </button>
                </div>

                {/* 错误详情（可折叠） */}
                {this.props.showDetails !== false && (
                  <details className="group">
                    <summary className="cursor-pointer text-gray-400 hover:text-gray-300 flex items-center">
                      <Bug className="w-4 h-4 mr-2" />
                      查看错误详情
                    </summary>
                    <div className="mt-4 p-4 bg-gray-900 rounded-lg overflow-x-auto">
                      <p className="text-red-400 font-mono text-sm mb-2">
                        {this.state.error?.toString()}
                      </p>
                      {this.state.errorInfo?.componentStack && (
                        <pre className="text-gray-500 text-xs whitespace-pre-wrap">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      )}
                    </div>
                  </details>
                )}
              </div>

              {/* 页脚 */}
              <div className="bg-gray-900/50 px-6 py-4 text-center">
                <p className="text-gray-500 text-sm">
                  如果问题持续存在，请联系技术支持
                </p>
              </div>
            </div>

            {/* 错误ID */}
            <p className="text-center text-gray-600 text-xs mt-4">
              错误ID: {this.state.errorId}
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * 高阶组件：为组件添加错误边界
 */
export function withErrorBoundary(WrappedComponent, errorBoundaryProps = {}) {
  return function WithErrorBoundaryComponent(props) {
    return (
      <ErrorBoundary {...errorBoundaryProps}>
        <WrappedComponent {...props} />
      </ErrorBoundary>
    );
  };
}

/**
 * 错误边界包装器 - 用于包装异步操作
 */
export function AsyncErrorBoundary({ children, fallback, onError }) {
  return (
    <ErrorBoundary fallback={fallback} onError={onError}>
      {children}
    </ErrorBoundary>
  );
}

export default ErrorBoundary;
