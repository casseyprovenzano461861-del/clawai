import React, { useState, useEffect } from 'react';
import { Activity, Cpu, HardDrive, Wifi, Battery, Thermometer } from 'lucide-react';
import { Card, CardTitle, CardContent } from './Card';

interface PerformanceMetrics {
  memory: {
    used: number;
    total: number;
    percent: number;
  };
  cpu: {
    usage: number;
    cores: number;
  };
  network: {
    upload: number;
    download: number;
  };
  battery?: {
    level: number;
    charging: boolean;
  };
  temperature?: number;
}

const PerformanceMonitor: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    memory: {
      used: 0,
      total: 0,
      percent: 0,
    },
    cpu: {
      usage: 0,
      cores: navigator.hardwareConcurrency || 4,
    },
    network: {
      upload: 0,
      download: 0,
    },
  });

  const [isMonitoring, setIsMonitoring] = useState(true);

  // 模拟性能数据更新
  useEffect(() => {
    if (!isMonitoring) return;

    const interval = setInterval(() => {
      // 模拟内存使用
      const totalMemory = 16 * 1024; // 16GB
      const usedMemory = Math.floor(Math.random() * totalMemory * 0.8) + totalMemory * 0.2;
      const memoryPercent = (usedMemory / totalMemory) * 100;

      // 模拟CPU使用率
      const cpuUsage = Math.floor(Math.random() * 100);

      // 模拟网络速度
      const uploadSpeed = Math.floor(Math.random() * 1000);
      const downloadSpeed = Math.floor(Math.random() * 5000);

      // 模拟电池状态
      const batteryLevel = Math.floor(Math.random() * 100);
      const isCharging = Math.random() > 0.5;

      // 模拟温度
      const temperature = 30 + Math.random() * 20;

      setMetrics({
        memory: {
          used: usedMemory,
          total: totalMemory,
          percent: memoryPercent,
        },
        cpu: {
          usage: cpuUsage,
          cores: navigator.hardwareConcurrency || 4,
        },
        network: {
          upload: uploadSpeed,
          download: downloadSpeed,
        },
        battery: {
          level: batteryLevel,
          charging: isCharging,
        },
        temperature,
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [isMonitoring]);

  // 格式化内存大小
  const formatMemory = (bytes: number): string => {
    if (bytes >= 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
    }
    if (bytes >= 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }
    if (bytes >= 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${bytes} B`;
  };

  // 格式化网络速度
  const formatNetworkSpeed = (bytesPerSecond: number): string => {
    if (bytesPerSecond >= 1024 * 1024) {
      return `${(bytesPerSecond / (1024 * 1024)).toFixed(1)} MB/s`;
    }
    if (bytesPerSecond >= 1024) {
      return `${(bytesPerSecond / 1024).toFixed(1)} KB/s`;
    }
    return `${bytesPerSecond} B/s`;
  };

  // 获取颜色基于百分比
  const getColorByPercent = (percent: number): string => {
    if (percent < 50) return 'text-success-500';
    if (percent < 80) return 'text-warning-500';
    return 'text-error-500';
  };

  // 获取背景颜色基于百分比
  const getBgColorByPercent = (percent: number): string => {
    if (percent < 50) return 'bg-success-500';
    if (percent < 80) return 'bg-warning-500';
    return 'bg-error-500';
  };

  return (
    <Card variant="elevated">
      <div className="flex items-center justify-between mb-4">
        <CardTitle>性能监控</CardTitle>
        <button
          onClick={() => setIsMonitoring(!isMonitoring)}
          className={`px-3 py-1 rounded-md text-sm font-medium ${
            isMonitoring
              ? 'bg-error-100 text-error-700 hover:bg-error-200'
              : 'bg-success-100 text-success-700 hover:bg-success-200'
          }`}
        >
          {isMonitoring ? '停止监控' : '开始监控'}
        </button>
      </div>
      
      <CardContent>
        <div className="space-y-6">
          {/* 内存使用 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <HardDrive className="h-5 w-5 text-gray-400 mr-2" />
                <span className="font-medium text-gray-700 dark:text-gray-300">内存使用</span>
              </div>
              <span className={`font-semibold ${getColorByPercent(metrics.memory.percent)}`}>
                {metrics.memory.percent.toFixed(1)}%
              </span>
            </div>
            <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`absolute top-0 left-0 h-full ${getBgColorByPercent(metrics.memory.percent)}`}
                style={{ width: `${Math.min(metrics.memory.percent, 100)}%` }}
              />
            </div>
            <div className="flex justify-between text-sm text-gray-500 dark:text-gray-400 mt-1">
              <span>{formatMemory(metrics.memory.used)} 已使用</span>
              <span>{formatMemory(metrics.memory.total)} 总计</span>
            </div>
          </div>

          {/* CPU使用率 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <Cpu className="h-5 w-5 text-gray-400 mr-2" />
                <span className="font-medium text-gray-700 dark:text-gray-300">CPU使用率</span>
              </div>
              <span className={`font-semibold ${getColorByPercent(metrics.cpu.usage)}`}>
                {metrics.cpu.usage}%
              </span>
            </div>
            <div className="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`absolute top-0 left-0 h-full ${getBgColorByPercent(metrics.cpu.usage)}`}
                style={{ width: `${Math.min(metrics.cpu.usage, 100)}%` }}
              />
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {metrics.cpu.cores} 核心处理器
            </div>
          </div>

          {/* 网络速度 */}
          <div>
            <div className="flex items-center mb-3">
              <Wifi className="h-5 w-5 text-gray-400 mr-2" />
              <span className="font-medium text-gray-700 dark:text-gray-300">网络速度</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">上传</div>
                <div className="text-lg font-semibold text-primary-600">
                  {formatNetworkSpeed(metrics.network.upload)}
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">下载</div>
                <div className="text-lg font-semibold text-success-600">
                  {formatNetworkSpeed(metrics.network.download)}
                </div>
              </div>
            </div>
          </div>

          {/* 电池和温度 */}
          <div className="grid grid-cols-2 gap-4">
            {metrics.battery && (
              <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <Battery className="h-5 w-5 text-gray-400" />
                  <span className={`text-sm font-medium ${
                    metrics.battery.level < 20 ? 'text-error-500' : 'text-gray-700 dark:text-gray-300'
                  }`}>
                    {metrics.battery.level}%
                  </span>
                </div>
                <div className="relative h-2 bg-gray-300 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`absolute top-0 left-0 h-full ${
                      metrics.battery.level < 20 ? 'bg-error-500' : 'bg-success-500'
                    }`}
                    style={{ width: `${metrics.battery.level}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {metrics.battery.charging ? '充电中' : '使用电池'}
                </div>
              </div>
            )}

            {metrics.temperature && (
              <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <Thermometer className="h-5 w-5 text-gray-400" />
                  <span className={`text-sm font-medium ${
                    metrics.temperature > 60 ? 'text-error-500' : 
                    metrics.temperature > 45 ? 'text-warning-500' : 'text-gray-700 dark:text-gray-300'
                  }`}>
                    {metrics.temperature.toFixed(1)}°C
                  </span>
                </div>
                <div className="relative h-2 bg-gray-300 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`absolute top-0 left-0 h-full ${
                      metrics.temperature > 60 ? 'bg-error-500' : 
                      metrics.temperature > 45 ? 'bg-warning-500' : 'bg-success-500'
                    }`}
                    style={{ width: `${Math.min(metrics.temperature, 100)}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {metrics.temperature > 60 ? '过热' : metrics.temperature > 45 ? '温暖' : '正常'}
                </div>
              </div>
            )}
          </div>

          {/* 状态指示器 */}
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Activity className={`h-4 w-4 mr-2 ${
                  isMonitoring ? 'text-success-500 animate-pulse' : 'text-gray-400'
                }`} />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  监控状态: {isMonitoring ? '运行中' : '已停止'}
                </span>
              </div>
              <div className="text-xs text-gray-500">
                更新间隔: 2秒
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PerformanceMonitor;