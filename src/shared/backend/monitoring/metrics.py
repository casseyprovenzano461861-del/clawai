"""
Prometheus指标管理器
解决指标重复注册问题，提供统一的指标接口
"""

import logging
from typing import Dict, Any, Optional, Callable

# 尝试导入Prometheus客户端，如果不可用则使用虚拟类
try:
    from prometheus_client import Counter, Histogram, Gauge, REGISTRY, CollectorRegistry
    from prometheus_client.metrics import MetricWrapperBase
    PROMETHEUS_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.debug("Prometheus客户端可用")
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # 定义虚拟类
    class MetricWrapperBase:
        pass

    class CollectorRegistry:
        def __init__(self):
            self.collectors = []

        def collect(self):
            return []

    REGISTRY = CollectorRegistry()

    # 定义虚拟指标类（将在后面定义）
    class Counter:
        pass

    class Histogram:
        pass

    class Gauge:
        pass

    logger = logging.getLogger(__name__)
    logger.warning("Prometheus客户端不可用，使用虚拟指标")

logger = logging.getLogger(__name__)


class MetricsManager:
    """指标管理器

    解决Prometheus指标重复注册问题，提供以下特性：
    1. 指标注册前检查，避免重复注册
    2. 支持多个注册表（默认使用全局注册表）
    3. 提供虚拟指标支持（用于测试或禁用指标）
    4. 统一的指标创建接口
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None, enable_metrics: bool = True):
        """
        初始化指标管理器

        Args:
            registry: Prometheus注册表，None则使用全局注册表
            enable_metrics: 是否启用指标收集，False时返回虚拟指标
        """
        self.registry = registry or REGISTRY
        self.enable_metrics = enable_metrics
        self.registered_metrics: Dict[str, MetricWrapperBase] = {}
        logger.info(f"指标管理器初始化完成 - 启用指标: {enable_metrics}")

    def _get_metric_name(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """获取指标的唯一标识符"""
        if labels:
            sorted_labels = sorted(labels.items())
            label_str = "_".join(f"{k}={v}" for k, v in sorted_labels)
            return f"{name}_{label_str}"
        return name

    def counter(
        self,
        name: str,
        documentation: str,
        labelnames: Optional[list] = None,
        namespace: str = "",
        subsystem: str = "",
        unit: str = "",
        **kwargs
    ) -> Counter:
        """创建或获取Counter指标"""
        # 如果Prometheus不可用，直接返回虚拟指标
        if not PROMETHEUS_AVAILABLE:
            logger.debug(f"Prometheus不可用，返回虚拟Counter指标: {name}")
            return DummyCounter(name, documentation, labelnames, **kwargs)

        metric_id = self._get_metric_name(name, kwargs.get("labels"))

        if metric_id in self.registered_metrics:
            metric = self.registered_metrics[metric_id]
            if isinstance(metric, Counter):
                logger.debug(f"重用已注册的Counter指标: {name}")
                return metric
            else:
                logger.warning(f"指标名称冲突: {name} 已存在但类型不同")

        if not self.enable_metrics:
            # 返回虚拟指标
            return DummyCounter(name, documentation, labelnames, **kwargs)

        try:
            # 尝试创建新的Counter
            labelnames = labelnames or []
            metric = Counter(
                name=name,
                documentation=documentation,
                labelnames=labelnames,
                namespace=namespace,
                subsystem=subsystem,
                unit=unit,
                registry=self.registry,
                **kwargs
            )
            self.registered_metrics[metric_id] = metric
            logger.debug(f"创建新的Counter指标: {name}")
            return metric
        except ValueError as e:
            # 指标已注册，尝试从注册表中获取
            logger.warning(f"Counter指标 {name} 可能已注册: {e}")
            try:
                # 从注册表中查找现有指标
                for collector in self.registry.collect():
                    for sample in collector.samples:
                        if sample.name == name:
                            # 返回虚拟指标，因为无法直接获取已注册的指标实例
                            logger.info(f"使用虚拟Counter指标: {name}")
                            return DummyCounter(name, documentation, labelnames, **kwargs)
            except:
                pass

            # 返回虚拟指标作为后备
            logger.info(f"使用虚拟Counter指标作为后备: {name}")
            return DummyCounter(name, documentation, labelnames, **kwargs)

    def gauge(
        self,
        name: str,
        documentation: str,
        labelnames: Optional[list] = None,
        namespace: str = "",
        subsystem: str = "",
        unit: str = "",
        **kwargs
    ) -> Gauge:
        """创建或获取Gauge指标"""
        # 如果Prometheus不可用，直接返回虚拟指标
        if not PROMETHEUS_AVAILABLE:
            logger.debug(f"Prometheus不可用，返回虚拟Gauge指标: {name}")
            return DummyGauge(name, documentation, labelnames, **kwargs)

        metric_id = self._get_metric_name(name, kwargs.get("labels"))

        if metric_id in self.registered_metrics:
            metric = self.registered_metrics[metric_id]
            if isinstance(metric, Gauge):
                logger.debug(f"重用已注册的Gauge指标: {name}")
                return metric
            else:
                logger.warning(f"指标名称冲突: {name} 已存在但类型不同")

        if not self.enable_metrics:
            # 返回虚拟指标
            return DummyGauge(name, documentation, labelnames, **kwargs)

        try:
            # 尝试创建新的Gauge
            labelnames = labelnames or []
            metric = Gauge(
                name=name,
                documentation=documentation,
                labelnames=labelnames,
                namespace=namespace,
                subsystem=subsystem,
                unit=unit,
                registry=self.registry,
                **kwargs
            )
            self.registered_metrics[metric_id] = metric
            logger.debug(f"创建新的Gauge指标: {name}")
            return metric
        except ValueError as e:
            # 指标已注册
            logger.warning(f"Gauge指标 {name} 可能已注册: {e}")
            logger.info(f"使用虚拟Gauge指标: {name}")
            return DummyGauge(name, documentation, labelnames, **kwargs)

    def histogram(
        self,
        name: str,
        documentation: str,
        labelnames: Optional[list] = None,
        namespace: str = "",
        subsystem: str = "",
        unit: str = "",
        buckets: Optional[list] = None,
        **kwargs
    ) -> Histogram:
        """创建或获取Histogram指标"""
        # 如果Prometheus不可用，直接返回虚拟指标
        if not PROMETHEUS_AVAILABLE:
            logger.debug(f"Prometheus不可用，返回虚拟Histogram指标: {name}")
            return DummyHistogram(name, documentation, labelnames, **kwargs)

        metric_id = self._get_metric_name(name, kwargs.get("labels"))

        if metric_id in self.registered_metrics:
            metric = self.registered_metrics[metric_id]
            if isinstance(metric, Histogram):
                logger.debug(f"重用已注册的Histogram指标: {name}")
                return metric
            else:
                logger.warning(f"指标名称冲突: {name} 已存在但类型不同")

        if not self.enable_metrics:
            # 返回虚拟指标
            return DummyHistogram(name, documentation, labelnames, **kwargs)

        try:
            # 尝试创建新的Histogram
            labelnames = labelnames or []
            metric = Histogram(
                name=name,
                documentation=documentation,
                labelnames=labelnames,
                namespace=namespace,
                subsystem=subsystem,
                unit=unit,
                buckets=buckets,
                registry=self.registry,
                **kwargs
            )
            self.registered_metrics[metric_id] = metric
            logger.debug(f"创建新的Histogram指标: {name}")
            return metric
        except ValueError as e:
            # 指标已注册
            logger.warning(f"Histogram指标 {name} 可能已注册: {e}")
            logger.info(f"使用虚拟Histogram指标: {name}")
            return DummyHistogram(name, documentation, labelnames, **kwargs)

    def get_metric(self, name: str) -> Optional[MetricWrapperBase]:
        """根据名称获取已注册的指标"""
        for metric_id, metric in self.registered_metrics.items():
            if metric_id.startswith(name):
                return metric
        return None

    def list_metrics(self) -> Dict[str, str]:
        """列出所有已注册的指标"""
        return {metric_id: type(metric).__name__ for metric_id, metric in self.registered_metrics.items()}


class DummyCounter:
    """虚拟Counter指标"""

    def __init__(self, name: str, documentation: str, labelnames: Optional[list] = None, **kwargs):
        self.name = name
        self.documentation = documentation
        self.labelnames = labelnames or []
        self._labels = {}

    def labels(self, **kwargs):
        self._labels.update(kwargs)
        return self

    def inc(self, amount: float = 1):
        pass

    def dec(self, amount: float = 1):
        pass


class DummyGauge:
    """虚拟Gauge指标"""

    def __init__(self, name: str, documentation: str, labelnames: Optional[list] = None, **kwargs):
        self.name = name
        self.documentation = documentation
        self.labelnames = labelnames or []
        self._labels = {}
        self._value = 0

    def labels(self, **kwargs):
        self._labels.update(kwargs)
        return self

    def set(self, value: float):
        self._value = value

    def inc(self, amount: float = 1):
        self._value += amount

    def dec(self, amount: float = 1):
        self._value -= amount

    def track_inprogress(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class DummyHistogram:
    """虚拟Histogram指标"""

    def __init__(self, name: str, documentation: str, labelnames: Optional[list] = None, **kwargs):
        self.name = name
        self.documentation = documentation
        self.labelnames = labelnames or []
        self._labels = {}

    def labels(self, **kwargs):
        self._labels.update(kwargs)
        return self

    def observe(self, value: float):
        pass


# 全局指标管理器实例
_metrics_manager: Optional[MetricsManager] = None


def get_metrics_manager(
    registry: Optional[CollectorRegistry] = None,
    enable_metrics: Optional[bool] = None
) -> MetricsManager:
    """获取全局指标管理器实例"""
    global _metrics_manager

    if _metrics_manager is None:
        # 从环境变量读取是否启用指标
        import os
        enable = enable_metrics
        if enable is None:
            enable_env = os.getenv("ENABLE_METRICS", "true").lower()
            enable = enable_env in ("true", "1", "yes", "on")

        _metrics_manager = MetricsManager(registry=registry, enable_metrics=enable)

    return _metrics_manager


def counter(name: str, documentation: str, **kwargs) -> Counter:
    """便捷函数：创建Counter指标"""
    return get_metrics_manager().counter(name, documentation, **kwargs)


def gauge(name: str, documentation: str, **kwargs) -> Gauge:
    """便捷函数：创建Gauge指标"""
    return get_metrics_manager().gauge(name, documentation, **kwargs)


def histogram(name: str, documentation: str, **kwargs) -> Histogram:
    """便捷函数：创建Histogram指标"""
    return get_metrics_manager().histogram(name, documentation, **kwargs)