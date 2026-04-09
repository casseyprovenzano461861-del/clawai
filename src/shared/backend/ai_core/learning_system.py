# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI学习能力系统
实现历史决策学习、成功率反馈学习和策略优化学习
"""

import json
import time
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import os
import math

from .multi_model_decision import DecisionResult, ModelDecision, MultiModelDecisionSystem


class LearningPhase(Enum):
    """学习阶段"""
    DATA_COLLECTION = "data_collection"      # 数据收集阶段
    PATTERN_RECOGNITION = "pattern_recognition"  # 模式识别阶段
    OPTIMIZATION = "optimization"            # 优化阶段
    VALIDATION = "validation"                # 验证阶段


class LearningStrategy(Enum):
    """学习策略"""
    REINFORCEMENT = "reinforcement"          # 强化学习
    SUPERVISED = "supervised"                # 监督学习
    ONLINE = "online"                        # 在线学习
    BATCH = "batch"                          # 批量学习


@dataclass
class LearningRecord:
    """学习记录"""
    record_id: str
    decision_id: str
    learning_type: str
    learning_data: Dict[str, Any]
    improvement_score: float  # 0.0-1.0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "record_id": self.record_id,
            "decision_id": self.decision_id,
            "learning_type": self.learning_type,
            "improvement_score": round(self.improvement_score, 4),
            "timestamp": datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            "data_summary": {
                k: str(v)[:100] + "..." if len(str(v)) > 100 else v
                for k, v in self.learning_data.items()
            }
        }


@dataclass
class ModelPerformanceMetrics:
    """模型性能指标"""
    model_name: str
    success_rate: float  # 0.0-1.0
    avg_confidence: float  # 0.0-1.0
    avg_response_time: float  # 秒
    total_decisions: int
    successful_decisions: int
    confidence_variance: float
    bias_score: float  # 偏差评分 (0.0-1.0)
    last_updated: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "model_name": self.model_name,
            "success_rate": round(self.success_rate, 4),
            "avg_confidence": round(self.avg_confidence, 4),
            "avg_response_time": round(self.avg_response_time, 2),
            "total_decisions": self.total_decisions,
            "successful_decisions": self.successful_decisions,
            "confidence_variance": round(self.confidence_variance, 4),
            "bias_score": round(self.bias_score, 4),
            "last_updated": datetime.fromtimestamp(self.last_updated).strftime('%Y-%m-%d %H:%M:%S')
        }


class DecisionPatternAnalyzer:
    """决策模式分析器"""
    
    def __init__(self):
        self.patterns = {}
        self.pattern_history = []
    
    def analyze_decision_patterns(self, decision_results: List[DecisionResult]) -> Dict[str, Any]:
        """分析决策模式"""
        if not decision_results:
            return {"error": "没有决策数据"}
        
        # 提取决策特征
        features = self._extract_decision_features(decision_results)
        
        # 分析时间模式
        temporal_patterns = self._analyze_temporal_patterns(decision_results)
        
        # 分析模型协作模式
        collaboration_patterns = self._analyze_collaboration_patterns(decision_results)
        
        # 分析决策质量趋势
        quality_trends = self._analyze_quality_trends(decision_results)
        
        # 识别常见模式
        common_patterns = self._identify_common_patterns(features)
        
        return {
            "feature_analysis": features,
            "temporal_patterns": temporal_patterns,
            "collaboration_patterns": collaboration_patterns,
            "quality_trends": quality_trends,
            "common_patterns": common_patterns,
            "total_decisions_analyzed": len(decision_results)
        }
    
    def _extract_decision_features(self, decision_results: List[DecisionResult]) -> Dict[str, Any]:
        """提取决策特征"""
        features = {
            "decision_status_distribution": {},
            "confidence_distribution": [],
            "model_count_distribution": [],
            "resolution_strategies": {},
            "decision_types": set()
        }
        
        for result in decision_results:
            # 决策状态分布
            status = result.status.value
            features["decision_status_distribution"][status] = (
                features["decision_status_distribution"].get(status, 0) + 1
            )
            
            # 置信度分布
            features["confidence_distribution"].append(result.confidence)
            
            # 模型数量分布
            model_count = len(result.model_decisions)
            features["model_count_distribution"].append(model_count)
            
            # 解决策略分布
            strategy = result.resolution_strategy
            features["resolution_strategies"][strategy] = (
                features["resolution_strategies"].get(strategy, 0) + 1
            )
            
            # 决策类型
            features["decision_types"].add(result.final_decision)
        
        # 计算统计摘要（纯Python实现）
        if features["confidence_distribution"]:
            confidences = features["confidence_distribution"]
            mean = sum(confidences) / len(confidences)
            
            # 计算标准差
            if len(confidences) > 1:
                variance = sum((x - mean) ** 2 for x in confidences) / (len(confidences) - 1)
                std_dev = math.sqrt(variance)
            else:
                std_dev = 0.0
            
            features["confidence_stats"] = {
                "mean": mean,
                "std": std_dev,
                "min": min(confidences),
                "max": max(confidences)
            }
        
        if features["model_count_distribution"]:
            model_counts = features["model_count_distribution"]
            mean = sum(model_counts) / len(model_counts)
            
            if len(model_counts) > 1:
                variance = sum((x - mean) ** 2 for x in model_counts) / (len(model_counts) - 1)
                std_dev = math.sqrt(variance)
            else:
                std_dev = 0.0
            
            features["model_count_stats"] = {
                "mean": mean,
                "std": std_dev,
                "min": min(model_counts),
                "max": max(model_counts)
            }
        
        # 转换集合为列表
        features["decision_types"] = list(features["decision_types"])
        
        return features
    
    def _analyze_temporal_patterns(self, decision_results: List[DecisionResult]) -> Dict[str, Any]:
        """分析时间模式"""
        if len(decision_results) < 2:
            return {"error": "数据不足分析时间模式"}
        
        # 按时间排序
        sorted_results = sorted(decision_results, key=lambda x: x.timestamp)
        
        # 计算时间间隔
        time_intervals = []
        for i in range(1, len(sorted_results)):
            interval = sorted_results[i].timestamp - sorted_results[i-1].timestamp
            time_intervals.append(interval)
        
        # 分析时间模式（纯Python实现）
        if time_intervals:
            avg_interval = sum(time_intervals) / len(time_intervals)
            if len(time_intervals) > 1:
                interval_mean = avg_interval
                interval_variance = sum((x - interval_mean) ** 2 for x in time_intervals) / (len(time_intervals) - 1)
                interval_std = math.sqrt(interval_variance)
            else:
                interval_std = 0.0
        else:
            avg_interval = 0
            interval_std = 0
        
        total_time_span = sorted_results[-1].timestamp - sorted_results[0].timestamp if sorted_results else 0
        
        patterns = {
            "avg_interval": avg_interval,
            "interval_std": interval_std,
            "total_time_span": total_time_span,
            "decision_frequency": len(sorted_results) / (total_time_span + 1e-6),
            "time_of_day_pattern": self._analyze_time_of_day_pattern(sorted_results)
        }
        
        return patterns
    
    def _analyze_time_of_day_pattern(self, decision_results: List[DecisionResult]) -> Dict[str, Any]:
        """分析一天中的时间模式"""
        hour_distribution = {str(h): 0 for h in range(24)}
        
        for result in decision_results:
            dt = datetime.fromtimestamp(result.timestamp)
            hour = str(dt.hour)
            hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
        
        # 找到高峰时段
        peak_hours = sorted(
            [(h, count) for h, count in hour_distribution.items() if count > 0],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return {
            "hour_distribution": hour_distribution,
            "peak_hours": peak_hours,
            "most_active_hour": peak_hours[0][0] if peak_hours else "未知"
        }
    
    def _analyze_collaboration_patterns(self, decision_results: List[DecisionResult]) -> Dict[str, Any]:
        """分析模型协作模式"""
        if not decision_results:
            return {"error": "没有决策数据"}
        
        # 分析模型组合
        model_combinations = {}
        model_success_pairs = {}
        
        for result in decision_results:
            # 获取参与模型
            models = [md.model_name for md in result.model_decisions]
            model_key = tuple(sorted(models))
            
            # 统计模型组合
            model_combinations[model_key] = model_combinations.get(model_key, 0) + 1
            
            # 分析模型对成功关系
            if result.status.value not in ["failed", "split"]:
                for i in range(len(models)):
                    for j in range(i+1, len(models)):
                        pair = tuple(sorted([models[i], models[j]]))
                        model_success_pairs[pair] = model_success_pairs.get(pair, 0) + 1
        
        # 找到最佳模型组合
        best_combination = max(model_combinations.items(), key=lambda x: x[1]) if model_combinations else ((), 0)
        
        # 找到最成功的模型对
        best_pair = max(model_success_pairs.items(), key=lambda x: x[1]) if model_success_pairs else ((), 0)
        
        return {
            "unique_model_combinations": len(model_combinations),
            "most_common_combination": {
                "models": list(best_combination[0]),
                "count": best_combination[1]
            },
            "model_success_pairs": {
                "best_pair": {
                    "models": list(best_pair[0]),
                    "success_count": best_pair[1]
                },
                "total_pairs": len(model_success_pairs)
            },
            "collaboration_network": self._build_collaboration_network(decision_results)
        }
    
    def _build_collaboration_network(self, decision_results: List[DecisionResult]) -> Dict[str, Any]:
        """构建协作网络"""
        network = {}
        
        for result in decision_results:
            models = [md.model_name for md in result.model_decisions]
            
            for model in models:
                if model not in network:
                    network[model] = {"collaborators": {}, "total_collaborations": 0}
                
                for collaborator in models:
                    if collaborator != model:
                        network[model]["collaborators"][collaborator] = (
                            network[model]["collaborators"].get(collaborator, 0) + 1
                        )
                        network[model]["total_collaborations"] += 1
        
        return network
    
    def _analyze_quality_trends(self, decision_results: List[DecisionResult]) -> Dict[str, Any]:
        """分析决策质量趋势"""
        if len(decision_results) < 3:
            return {"error": "数据不足分析趋势"}
        
        # 按时间排序
        sorted_results = sorted(decision_results, key=lambda x: x.timestamp)
        
        # 提取时间序列
        timestamps = [r.timestamp for r in sorted_results]
        confidences = [r.confidence for r in sorted_results]
        
        # 计算移动平均（纯Python实现）
        window_size = min(5, len(sorted_results))
        moving_avg = []
        for i in range(len(confidences) - window_size + 1):
            window = confidences[i:i+window_size]
            moving_avg.append(sum(window) / len(window))
        
        # 分析趋势
        if len(confidences) >= 2:
            trend_slope = self._calculate_trend_slope(confidences)
        else:
            trend_slope = 0
        
        # 计算波动率（标准差）
        if len(confidences) > 1:
            mean_confidence = sum(confidences) / len(confidences)
            variance = sum((x - mean_confidence) ** 2 for x in confidences) / (len(confidences) - 1)
            volatility = math.sqrt(variance)
        else:
            volatility = 0
        
        return {
            "confidence_trend": {
                "initial": confidences[0] if confidences else 0,
                "final": confidences[-1] if confidences else 0,
                "trend_slope": trend_slope,
                "is_improving": trend_slope > 0.01,
                "is_declining": trend_slope < -0.01
            },
            "moving_average": moving_avg[-5:] if moving_avg else [],
            "volatility": volatility
        }
    
    def _calculate_trend_slope(self, values: List[float]) -> float:
        """计算趋势斜率（纯Python线性回归）"""
        n = len(values)
        if n < 2:
            return 0
        
        # 简单线性回归：y = slope * x + intercept
        x = list(range(n))
        y = values
        
        # 计算均值
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        # 计算斜率
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
        
        slope = numerator / denominator
        return slope
    
    def _identify_common_patterns(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别常见模式"""
        patterns = []
        
        # 模式1: 高置信度共识决策
        if features.get("confidence_stats", {}).get("mean", 0) > 0.8:
            patterns.append({
                "pattern_type": "high_confidence_consensus",
                "description": "系统倾向于做出高置信度的共识决策",
                "confidence": 0.85
            })
        
        # 模式2: 多模型协作
        avg_models = features.get("model_count_stats", {}).get("mean", 0)
        if avg_models > 2.5:
            patterns.append({
                "pattern_type": "multi_model_collaboration",
                "description": "决策通常涉及多个模型协作",
                "confidence": 0.75
            })
        
        # 模式3: 特定解决策略偏好
        strategies = features.get("resolution_strategies", {})
        if strategies:
            top_strategy = max(strategies.items(), key=lambda x: x[1])
            if top_strategy[1] / sum(strategies.values()) > 0.6:
                patterns.append({
                    "pattern_type": "strategy_preference",
                    "description": f"系统偏好使用'{top_strategy[0]}'解决策略",
                    "confidence": 0.8
                })
        
        # 模式4: 决策类型多样性
        decision_types = features.get("decision_types", [])
        if len(decision_types) > 5:
            patterns.append({
                "pattern_type": "decision_diversity",
                "description": "系统能够处理多种类型的决策",
                "confidence": 0.7
            })
        
        return patterns


class AILearningSystem:
    """
    AI学习能力系统
    实现历史决策学习、成功率反馈学习和策略优化学习
    """
    
    def __init__(self, decision_system: MultiModelDecisionSystem, 
                 learning_rate: float = 0.1, memory_size: int = 1000):
        """
        初始化AI学习系统
        
        Args:
            decision_system: 决策系统实例
            learning_rate: 学习率 (0.0-1.0)
            memory_size: 记忆容量
        """
        self.decision_system = decision_system
        self.learning_rate = learning_rate
        self.memory_size = memory_size
        
        # 学习组件
        self.pattern_analyzer = DecisionPatternAnalyzer()
        self.performance_metrics: Dict[str, ModelPerformanceMetrics] = {}
        self.learning_history: List[LearningRecord] = []
        
        # 学习状态
        self.current_phase = LearningPhase.DATA_COLLECTION
        self.learning_strategy = LearningStrategy.ONLINE
        self.total_learning_cycles = 0
        self.average_improvement = 0.0
        
        # 学习参数
        self.consensus_threshold_history = []
        self.majority_threshold_history = []
        self.model_weight_history = {}
        
        # 初始化性能指标
        self._init_performance_metrics()
    
    def _init_performance_metrics(self):
        """初始化性能指标"""
        # 从决策系统获取模型列表
        model_names = list(self.decision_system.model_weights.keys())
        
        for model_name in model_names:
            self.performance_metrics[model_name] = ModelPerformanceMetrics(
                model_name=model_name,
                success_rate=0.5,  # 初始成功率
                avg_confidence=0.5,  # 初始平均置信度
                avg_response_time=5.0,  # 初始响应时间
                total_decisions=0,
                successful_decisions=0,
                confidence_variance=0.1,
                bias_score=0.5
            )
    
    def learn_from_decision(self, decision_result: DecisionResult, 
                           success_feedback: bool) -> LearningRecord:
        """
        从单个决策中学习
        
        Args:
            decision_result: 决策结果
            success_feedback: 成功反馈 (True/False)
            
        Returns:
            学习记录
        """
        record_id = f"learn_{int(time.time())}_{hash(str(decision_result)) % 10000:04d}"
        
        # 收集学习数据
        learning_data = self._collect_learning_data(decision_result, success_feedback)
        
        # 更新模型性能指标
        self._update_model_performance(decision_result, success_feedback)
        
        # 分析决策模式
        pattern_analysis = self.pattern_analyzer.analyze_decision_patterns([decision_result])
        
        # 学习优化
        improvement_score = self._perform_learning_optimization(learning_data)
        
        # 创建学习记录
        learning_record = LearningRecord(
            record_id=record_id,
            decision_id=str(hash(str(decision_result))),
            learning_type="single_decision",
            learning_data={
                "decision_data": learning_data,
                "pattern_analysis": pattern_analysis,
                "success_feedback": success_feedback,
                "improvement_score": improvement_score
            },
            improvement_score=improvement_score,
            metadata={
                "phase": self.current_phase.value,
                "strategy": self.learning_strategy.value
            }
        )
        
        # 记录学习历史
        self.learning_history.append(learning_record)
        self.total_learning_cycles += 1
        
        # 更新学习阶段
        self._update_learning_phase()
        
        return learning_record
    
    def learn_from_history(self, decision_history: List[DecisionResult], 
                          success_history: List[bool]) -> LearningRecord:
        """
        从历史决策中批量学习
        
        Args:
            decision_history: 决策历史
            success_history: 成功历史
            
        Returns:
            学习记录
        """
        if len(decision_history) != len(success_history):
            raise ValueError("决策历史与成功历史长度不匹配")
        
        record_id = f"batch_learn_{int(time.time())}_{hash(str(decision_history)) % 10000:04d}"
        
        # 批量学习数据
        batch_data = []
        for i, (decision, success) in enumerate(zip(decision_history, success_history)):
            data = self._collect_learning_data(decision, success)
            data["sequence_index"] = i
            batch_data.append(data)
        
        # 分析历史模式
        pattern_analysis = self.pattern_analyzer.analyze_decision_patterns(decision_history)
        
        # 批量更新模型性能
        for decision, success in zip(decision_history, success_history):
            self._update_model_performance(decision, success)
        
        # 批量学习优化
        improvement_score = self._perform_batch_learning_optimization(batch_data)
        
        # 调整决策系统参数
        self._adjust_decision_system_parameters(pattern_analysis)
        
        # 创建学习记录
        learning_record = LearningRecord(
            record_id=record_id,
            decision_id="batch_" + str(hash(str(decision_history))),
            learning_type="batch_history",
            learning_data={
                "batch_size": len(decision_history),
                "pattern_analysis": pattern_analysis,
                "success_rate": sum(success_history) / len(success_history) if success_history else 0,
                "improvement_score": improvement_score
            },
            improvement_score=improvement_score,
            metadata={
                "phase": self.current_phase.value,
                "strategy": LearningStrategy.BATCH.value
            }
        )
        
        # 记录学习历史
        self.learning_history.append(learning_record)
        self.total_learning_cycles += 1
        
        # 更新学习阶段
        self._update_learning_phase()
        
        return learning_record
    
    def optimize_decision_strategy(self) -> Dict[str, Any]:
        """
        优化决策策略
        
        Returns:
            优化结果
        """
        # 收集当前性能数据
        performance_data = {}
        for model_name, metrics in self.performance_metrics.items():
            performance_data[model_name] = {
                "success_rate": metrics.success_rate,
                "avg_response_time": metrics.avg_response_time
            }
        
        # 更新模型权重
        self.decision_system.update_model_weights(performance_data)
        
        # 调整决策阈值
        threshold_optimization = self._optimize_decision_thresholds()
        
        # 分析优化效果
        optimization_result = {
            "model_weights_updated": self.decision_system.model_weights.copy(),
            "threshold_optimization": threshold_optimization,
            "performance_metrics": {
                name: metrics.to_dict() 
                for name, metrics in self.performance_metrics.items()
            },
            "learning_phase": self.current_phase.value,
            "total_learning_cycles": self.total_learning_cycles
        }
        
        # 记录优化历史
        self.consensus_threshold_history.append(
            self.decision_system.consensus_threshold
        )
        self.majority_threshold_history.append(
            self.decision_system.majority_threshold
        )
        
        # 记录模型权重历史
        for model_name, weight in self.decision_system.model_weights.items():
            if model_name not in self.model_weight_history:
                self.model_weight_history[model_name] = []
            self.model_weight_history[model_name].append(weight)
        
        return optimization_result
    
    def _collect_learning_data(self, decision_result: DecisionResult, 
                              success_feedback: bool) -> Dict[str, Any]:
        """收集学习数据"""
        return {
            "decision_id": str(hash(str(decision_result))),
            "final_decision": decision_result.final_decision,
            "status": decision_result.status.value,
            "confidence": decision_result.confidence,
            "model_count": len(decision_result.model_decisions),
            "resolution_strategy": decision_result.resolution_strategy,
            "success_feedback": success_feedback,
            "timestamp": decision_result.timestamp,
            "model_decisions": [
                {
                    "model_name": md.model_name,
                    "decision": md.decision,
                    "confidence": md.confidence,
                    "reasoning_length": len(md.reasoning)
                }
                for md in decision_result.model_decisions
            ]
        }
    
    def _update_model_performance(self, decision_result: DecisionResult, 
                                 success_feedback: bool):
        """更新模型性能指标"""
        for model_decision in decision_result.model_decisions:
            model_name = model_decision.model_name
            
            if model_name not in self.performance_metrics:
                self.performance_metrics[model_name] = ModelPerformanceMetrics(
                    model_name=model_name,
                    success_rate=0.5,
                    avg_confidence=0.5,
                    avg_response_time=5.0,
                    total_decisions=0,
                    successful_decisions=0,
                    confidence_variance=0.1,
                    bias_score=0.5
                )
            
            metrics = self.performance_metrics[model_name]
            
            # 更新统计
            metrics.total_decisions += 1
            if success_feedback:
                metrics.successful_decisions += 1
            
            # 更新成功率
            metrics.success_rate = (
                metrics.successful_decisions / metrics.total_decisions
                if metrics.total_decisions > 0 else 0.5
            )
            
            # 更新平均置信度
            old_avg = metrics.avg_confidence
            total_weight = metrics.total_decisions - 1
            metrics.avg_confidence = (
                (old_avg * total_weight + model_decision.confidence) / metrics.total_decisions
                if metrics.total_decisions > 0 else model_decision.confidence
            )
            
            # 更新置信度方差（纯Python实现）
            # 简化处理：当前只考虑单个置信度，不计算方差，保持原值
            # 后续可以考虑收集历史置信度进行方差计算
            pass
            
            # 更新偏差评分
            metrics.bias_score = self._calculate_bias_score(model_decision, success_feedback)
            
            # 更新时间戳
            metrics.last_updated = time.time()
    
    def _calculate_bias_score(self, model_decision: ModelDecision, 
                             success_feedback: bool) -> float:
        """计算偏差评分"""
        # 简化的偏差评分计算
        bias_factors = []
        
        # 置信度偏差
        if model_decision.confidence > 0.9:
            bias_factors.append(0.3)  # 过度自信
        elif model_decision.confidence < 0.3:
            bias_factors.append(0.2)  # 信心不足
        
        # 理由长度偏差
        reasoning_len = len(model_decision.reasoning)
        if reasoning_len < 50:
            bias_factors.append(0.2)  # 理由过短
        elif reasoning_len > 500:
            bias_factors.append(0.1)  # 理由过长
        
        # 成功反馈偏差
        if not success_feedback and model_decision.confidence > 0.7:
            bias_factors.append(0.4)  # 高置信度但失败
        
        # 计算综合偏差评分
        if bias_factors:
            bias_score = sum(bias_factors) / len(bias_factors)
        else:
            bias_score = 0.1  # 低偏差
        
        return min(1.0, bias_score)
    
    def _perform_learning_optimization(self, learning_data: Dict[str, Any]) -> float:
        """执行学习优化"""
        improvement = 0.0
        
        # 根据成功反馈调整
        if learning_data.get("success_feedback", False):
            # 成功案例学习
            improvement += 0.2
            
            # 强化成功模式
            if learning_data["confidence"] > 0.7:
                improvement += 0.1
        else:
            # 失败案例学习
            improvement += 0.3  # 从失败中学到更多
            
            # 分析失败原因
            if learning_data["confidence"] > 0.7:
                improvement += 0.2  # 高置信度失败需要更多调整
        
        # 根据决策状态调整
        status = learning_data.get("status", "")
        if status == "consensus":
            improvement += 0.1
        elif status == "failed":
            improvement += 0.3
        
        # 限制在0-1范围内
        return min(1.0, improvement * self.learning_rate)
    
    def _perform_batch_learning_optimization(self, batch_data: List[Dict[str, Any]]) -> float:
        """执行批量学习优化"""
        if not batch_data:
            return 0.0
        
        # 计算平均改进分数
        individual_improvements = []
        
        for data in batch_data:
            improvement = self._perform_learning_optimization(data)
            individual_improvements.append(improvement)
        
        # 计算批量学习效果（纯Python实现）
        if individual_improvements:
            avg_improvement = sum(individual_improvements) / len(individual_improvements)
        else:
            avg_improvement = 0
        
        # 批量学习可能有协同效应
        batch_synergy = min(0.3, len(batch_data) * 0.05)
        
        total_improvement = avg_improvement + batch_synergy
        
        # 更新平均改进分数
        if self.total_learning_cycles > 0:
            self.average_improvement = (
                (self.average_improvement * (self.total_learning_cycles - 1) + total_improvement) 
                / self.total_learning_cycles
            )
        else:
            self.average_improvement = total_improvement
        
        return min(1.0, total_improvement)
    
    def _adjust_decision_system_parameters(self, pattern_analysis: Dict[str, Any]):
        """调整决策系统参数"""
        # 根据模式分析调整阈值
        confidence_stats = pattern_analysis.get("feature_analysis", {}).get("confidence_stats", {})
        
        if confidence_stats:
            avg_confidence = confidence_stats.get("mean", 0.5)
            
            # 根据平均置信度调整共识阈值
            if avg_confidence > 0.7:
                # 高置信度环境，可以降低阈值
                self.decision_system.consensus_threshold = max(0.6, avg_confidence - 0.1)
            elif avg_confidence < 0.4:
                # 低置信度环境，需要提高阈值
                self.decision_system.consensus_threshold = min(0.8, avg_confidence + 0.2)
            
            # 调整多数阈值
            self.decision_system.majority_threshold = self.decision_system.consensus_threshold * 0.7
    
    def _optimize_decision_thresholds(self) -> Dict[str, Any]:
        """优化决策阈值"""
        # 基于历史性能优化阈值
        if len(self.consensus_threshold_history) >= 3:
            # 分析阈值历史（纯Python实现）
            recent_thresholds = self.consensus_threshold_history[-3:]
            
            # 计算平均值
            avg_threshold = sum(recent_thresholds) / len(recent_thresholds)
            
            # 计算标准差
            if len(recent_thresholds) > 1:
                threshold_variance = sum((x - avg_threshold) ** 2 for x in recent_thresholds) / (len(recent_thresholds) - 1)
                threshold_std = math.sqrt(threshold_variance)
            else:
                threshold_std = 0
            
            # 动态调整
            if threshold_std > 0.1:
                # 波动大，需要稳定
                new_threshold = avg_threshold
            else:
                # 稳定状态，可以微调优化
                success_rate = self._calculate_overall_success_rate()
                
                if success_rate > 0.8:
                    # 高成功率，可以降低阈值提高效率
                    new_threshold = max(0.6, avg_threshold - 0.05)
                elif success_rate < 0.5:
                    # 低成功率，需要提高阈值确保质量
                    new_threshold = min(0.9, avg_threshold + 0.05)
                else:
                    new_threshold = avg_threshold
            
            self.decision_system.consensus_threshold = new_threshold
            self.decision_system.majority_threshold = new_threshold * 0.7
            
            return {
                "old_consensus_threshold": self.consensus_threshold_history[-1],
                "new_consensus_threshold": new_threshold,
                "new_majority_threshold": new_threshold * 0.7,
                "optimization_reason": "基于历史性能动态调整"
            }
        
        return {"optimization_reason": "历史数据不足，保持默认阈值"}
    
    def _calculate_overall_success_rate(self) -> float:
        """计算总体成功率"""
        total_decisions = sum(m.total_decisions for m in self.performance_metrics.values())
        total_success = sum(m.successful_decisions for m in self.performance_metrics.values())
        
        if total_decisions > 0:
            return total_success / total_decisions
        return 0.5  # 默认成功率
    
    def _update_learning_phase(self):
        """更新学习阶段"""
        if self.total_learning_cycles < 10:
            self.current_phase = LearningPhase.DATA_COLLECTION
        elif self.total_learning_cycles < 30:
            self.current_phase = LearningPhase.PATTERN_RECOGNITION
        elif self.total_learning_cycles < 50:
            self.current_phase = LearningPhase.OPTIMIZATION
        else:
            self.current_phase = LearningPhase.VALIDATION
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """获取学习摘要"""
        return {
            "total_learning_cycles": self.total_learning_cycles,
            "current_phase": self.current_phase.value,
            "learning_strategy": self.learning_strategy.value,
            "average_improvement": round(self.average_improvement, 4),
            "performance_metrics": {
                name: metrics.to_dict() 
                for name, metrics in self.performance_metrics.items()
            },
            "decision_system_parameters": {
                "consensus_threshold": self.decision_system.consensus_threshold,
                "majority_threshold": self.decision_system.majority_threshold,
                "model_weights": self.decision_system.model_weights
            },
            "recent_learning_history": [
                record.to_dict() 
                for record in self.learning_history[-5:]
            ] if self.learning_history else []
        }
    
    def export_learning_data(self, filepath: str):
        """导出学习数据"""
        export_data = {
            "export_time": datetime.now().isoformat(),
            "learning_system_summary": self.get_learning_summary(),
            "pattern_analysis": self.pattern_analyzer.patterns,
            "learning_history": [
                record.to_dict() for record in self.learning_history[-100:]
            ],
            "threshold_history": {
                "consensus_threshold": self.consensus_threshold_history,
                "majority_threshold": self.majority_threshold_history,
                "model_weights": self.model_weight_history
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def save_model(self, filepath: str):
        """保存学习模型"""
        model_data = {
            "performance_metrics": {
                name: {
                    "success_rate": metrics.success_rate,
                    "avg_confidence": metrics.avg_confidence,
                    "avg_response_time": metrics.avg_response_time,
                    "total_decisions": metrics.total_decisions,
                    "successful_decisions": metrics.successful_decisions,
                    "confidence_variance": metrics.confidence_variance,
                    "bias_score": metrics.bias_score
                }
                for name, metrics in self.performance_metrics.items()
            },
            "decision_system_weights": self.decision_system.model_weights,
            "consensus_threshold": self.decision_system.consensus_threshold,
            "majority_threshold": self.decision_system.majority_threshold,
            "learning_parameters": {
                "learning_rate": self.learning_rate,
                "total_learning_cycles": self.total_learning_cycles,
                "average_improvement": self.average_improvement
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, ensure_ascii=False, indent=2)
    
    def load_model(self, filepath: str):
        """加载学习模型"""
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
            
            # 加载性能指标
            for name, metrics_data in model_data.get("performance_metrics", {}).items():
                if name in self.performance_metrics:
                    self.performance_metrics[name].success_rate = metrics_data.get("success_rate", 0.5)
                    self.performance_metrics[name].avg_confidence = metrics_data.get("avg_confidence", 0.5)
                    self.performance_metrics[name].total_decisions = metrics_data.get("total_decisions", 0)
                    self.performance_metrics[name].successful_decisions = metrics_data.get("successful_decisions", 0)
            
            # 加载决策系统权重
            weights = model_data.get("decision_system_weights", {})
            for model_name, weight in weights.items():
                if model_name in self.decision_system.model_weights:
                    self.decision_system.model_weights[model_name] = weight
            
            # 加载阈值
            self.decision_system.consensus_threshold = model_data.get("consensus_threshold", 0.7)
            self.decision_system.majority_threshold = model_data.get("majority_threshold", 0.5)
            
            # 加载学习参数
            self.total_learning_cycles = model_data.get("learning_parameters", {}).get("total_learning_cycles", 0)
            self.average_improvement = model_data.get("learning_parameters", {}).get("average_improvement", 0.0)
            
            return True
        except Exception as e:
            print(f"加载模型失败: {e}")
            return False


# 测试函数
def test_learning_system():
    """测试AI学习系统"""
    print("=" * 80)
    print("AI学习能力系统测试")
    print("=" * 80)
    
    # 创建决策系统
    from .multi_model_decision import MultiModelDecisionSystem, ModelDecision, DecisionResult, DecisionStatus
    
    decision_system = MultiModelDecisionSystem()
    
    # 创建学习系统
    learning_system = AILearningSystem(decision_system, learning_rate=0.2)
    
    # 创建测试决策数据
    test_decisions = []
    test_success = []
    
    for i in range(5):
        # 创建模拟决策
        model_decisions = [
            ModelDecision(
                model_name="deepseek",
                decision=f"attack_type_{i}",
                confidence=0.7 + i * 0.05,
                reasoning=f"测试决策{i}: 攻击类型{i}，置信度{0.7 + i * 0.05}"
            ),
            ModelDecision(
                model_name="openai",
                decision=f"attack_type_{i}",
                confidence=0.65 + i * 0.04,
                reasoning=f"测试决策{i}: 同意攻击类型{i}"
            )
        ]
        
        # 生成决策结果
        decision_result = decision_system.make_decision(model_decisions)
        test_decisions.append(decision_result)
        
        # 模拟成功反馈（前3个成功，后2个失败）
        success = i < 3
        test_success.append(success)
    
    # 测试1: 单次决策学习
    print("\n1. 单次决策学习测试:")
    for i, (decision, success) in enumerate(zip(test_decisions[:2], test_success[:2])):
        learning_record = learning_system.learn_from_decision(decision, success)
        print(f"决策{i+1}学习记录:")
        print(f"  学习类型: {learning_record.learning_type}")
        print(f"  改进分数: {learning_record.improvement_score:.3f}")
        print(f"  学习阶段: {learning_system.current_phase.value}")
    
    # 测试2: 批量历史学习
    print("\n2. 批量历史学习测试:")
    batch_record = learning_system.learn_from_history(test_decisions, test_success)
    print(f"批量学习记录:")
    print(f"  学习类型: {batch_record.learning_type}")
    print(f"  批量大小: {batch_record.learning_data['batch_size']}")
    print(f"  成功率: {batch_record.learning_data['success_rate']:.2%}")
    print(f"  改进分数: {batch_record.improvement_score:.3f}")
    
    # 测试3: 决策策略优化
    print("\n3. 决策策略优化测试:")
    optimization_result = learning_system.optimize_decision_strategy()
    print(f"优化结果:")
    print(f"  共识阈值: {optimization_result['model_weights_updated']}")
    print(f"  学习阶段: {optimization_result['learning_phase']}")
    print(f"  学习周期: {optimization_result['total_learning_cycles']}")
    
    # 测试4: 获取学习摘要
    print("\n4. 学习摘要测试:")
    summary = learning_system.get_learning_summary()
    print(f"总学习周期: {summary['total_learning_cycles']}")
    print(f"当前阶段: {summary['current_phase']}")
    print(f"平均改进: {summary['average_improvement']:.3f}")
    
    # 显示模型性能
    print("\n模型性能指标:")
    for model_name, metrics in summary['performance_metrics'].items():
        print(f"  {model_name}:")
        print(f"    成功率: {metrics['success_rate']:.2%}")
        print(f"    平均置信度: {metrics['avg_confidence']:.3f}")
        print(f"    总决策数: {metrics['total_decisions']}")
    
    # 测试5: 模式分析
    print("\n5. 决策模式分析测试:")
    pattern_analysis = learning_system.pattern_analyzer.analyze_decision_patterns(test_decisions)
    print(f"分析决策数: {pattern_analysis['total_decisions_analyzed']}")
    print(f"常见模式数量: {len(pattern_analysis['common_patterns'])}")
    
    for pattern in pattern_analysis['common_patterns'][:2]:
        print(f"  模式: {pattern['pattern_type']}")
        print(f"    描述: {pattern['description']}")
        print(f"    置信度: {pattern['confidence']:.2f}")
    
    # 测试6: 导出和保存
    print("\n6. 导出功能测试:")
    try:
        # 创建临时目录
        import tempfile
        temp_dir = tempfile.gettempdir()
        
        # 导出学习数据
        export_path = os.path.join(temp_dir, "clawai_learning_export.json")
        learning_system.export_learning_data(export_path)
        print(f"学习数据已导出到: {export_path}")
        
        # 保存模型
        model_path = os.path.join(temp_dir, "clawai_learning_model.pkl")
        learning_system.save_model(model_path)
        print(f"学习模型已保存到: {model_path}")
        
        # 加载模型
        new_learning_system = AILearningSystem(decision_system)
        if new_learning_system.load_model(model_path):
            print("学习模型加载成功")
        else:
            print("学习模型加载失败")
        
    except Exception as e:
        print(f"导出测试失败: {e}")
    
    print("\n" + "=" * 80)
    print("AI学习能力系统测试完成")


if __name__ == "__main__":
    test_learning_system()