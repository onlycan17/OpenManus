"""
피드백 패턴을 분석하고 매칭하는 모듈입니다.
"""

from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from .models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    ImprovementType
)

class PatternMatcher:
    """
    피드백 패턴을 분석하고 매칭하는 클래스입니다.
    멀티프로세싱과 캐싱을 통해 성능을 최적화합니다.
    """

    def __init__(self):
        """PatternMatcher 객체를 초기화합니다."""
        # 패턴 매칭을 위한 임계값 설정
        self.frequency_threshold = 3  # 패턴으로 인정할 최소 발생 빈도
        self.time_window = timedelta(days=7)  # 패턴 분석 시간 윈도우
        self.similarity_threshold = 0.7  # 유사성 판단 임계값

        # 병렬 처리를 위한 설정
        self.max_workers = mp.cpu_count()
        self._pattern_cache = {}

    def find_patterns(self, feedbacks: List[Feedback]) -> List[Dict]:
        """
        피드백 목록에서 패턴을 찾습니다. 병렬 처리를 통해 성능을 최적화합니다.

        Args:
            feedbacks: 분석할 피드백 목록

        Returns:
            List[Dict]: 발견된 패턴 목록
        """
        # 캐시 키 생성
        cache_key = self._generate_cache_key(feedbacks)
        if cache_key in self._pattern_cache:
            return self._pattern_cache[cache_key]

        patterns = []

        # 병렬 처리를 위한 작업 정의
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 각 패턴 분석 작업을 병렬로 실행
            future_time = executor.submit(self._find_time_based_patterns, feedbacks)
            future_type = executor.submit(self._find_type_based_patterns, feedbacks)
            future_metric = executor.submit(self._find_metric_based_patterns, feedbacks)

            # 결과 수집
            patterns.extend(future_time.result())
            patterns.extend(future_type.result())
            patterns.extend(future_metric.result())

        # 결과 캐싱
        self._pattern_cache[cache_key] = patterns
        return patterns

    def _generate_cache_key(self, feedbacks: List[Feedback]) -> str:
        """피드백 목록에 대한 캐시 키를 생성합니다."""
        # 피드백의 핵심 속성을 기반으로 캐시 키 생성
        key_components = [
            f.id for f in sorted(feedbacks, key=lambda x: x.id)
        ]
        return "|".join(key_components)

    @lru_cache(maxsize=128)
    def _find_time_based_patterns(self, feedbacks: List[Feedback]) -> List[Dict]:
        """시간 기반 패턴을 찾습니다. LRU 캐싱을 적용합니다."""
        patterns = []
        now = datetime.now()

        # 넘파이 배열로 변환하여 처리 속도 향상
        recent_feedbacks = [f for f in feedbacks if now - f.created_at <= self.time_window]
        hours = np.array([f.created_at.hour for f in recent_feedbacks])

        # 시간대별 발생 빈도 분석 (넘파이 사용)
        unique_hours, counts = np.unique(hours, return_counts=True)

        # 빈발 시간대 패턴 추출
        for hour, count in zip(unique_hours, counts):
            if count >= self.frequency_threshold:
                patterns.append({
                    "type": "time_based",
                    "hour": int(hour),
                    "count": int(count),
                    "description": f"시간대 {int(hour)}시에 피드백이 자주 발생함"
                })

        return patterns

    @lru_cache(maxsize=128)
    def _find_type_based_patterns(self, feedbacks: List[Feedback]) -> List[Dict]:
        """유형 기반 패턴을 찾습니다. LRU 캐싱을 적용합니다."""
        patterns = []

        # 넘파이 배열로 변환하여 처리 속도 향상
        feedback_types = np.array([f.type for f in feedbacks])
        unique_types, type_counts = np.unique(feedback_types, return_counts=True)

        for feedback_type, count in zip(unique_types, type_counts):
            if count >= self.frequency_threshold:
                # 해당 유형의 피드백만 필터링
                type_feedbacks = [f for f in feedbacks if f.type == feedback_type]

                # 심각도 분포 분석
                severities = np.array([f.severity for f in type_feedbacks])
                unique_severities, severity_counts = np.unique(severities, return_counts=True)
                main_severity = unique_severities[np.argmax(severity_counts)]

                patterns.append({
                    "type": "type_based",
                    "feedback_type": feedback_type,
                    "count": int(count),
                    "main_severity": main_severity,
                    "description": f"{feedback_type.value} 유형의 피드백이 빈번하게 발생하며, 주로 {main_severity.value} 심각도를 보임"
                })

        return patterns

    @lru_cache(maxsize=128)
    def _find_metric_based_patterns(self, feedbacks: List[Feedback]) -> List[Dict]:
        """메트릭 기반 패턴을 찾습니다. LRU 캐싱을 적용합니다."""
        patterns = []

        # 메트릭별 데이터 수집
        metric_data = defaultdict(list)
        for feedback in feedbacks:
            for metric_name, value in feedback.metrics.items():
                if isinstance(value, (int, float)):
                    metric_data[metric_name].append(value)

        # 메트릭별 패턴 분석 (넘파이 사용)
        for metric_name, values in metric_data.items():
            if len(values) >= self.frequency_threshold:
                values_array = np.array(values)
                avg_value = np.mean(values_array)
                max_value = np.max(values_array)
                min_value = np.min(values_array)

                # 이상치 탐지 (IQR 방법 사용)
                q1, q3 = np.percentile(values_array, [25, 75])
                iqr = q3 - q1
                upper_bound = q3 + 1.5 * iqr
                anomalies = values_array[values_array > upper_bound]

                if len(anomalies) > 0:
                    patterns.append({
                        "type": "metric_based",
                        "metric_name": metric_name,
                        "avg_value": float(avg_value),
                        "max_value": float(max_value),
                        "min_value": float(min_value),
                        "anomaly_count": len(anomalies),
                        "anomaly_threshold": float(upper_bound),
                        "description": (
                            f"{metric_name} 메트릭에서 {len(anomalies)}개의 이상치가 발견됨 "
                            f"(임계값: {upper_bound:.2f}, 평균: {avg_value:.2f})"
                        )
                    })

        return patterns

    def _calculate_pattern_weight(self, pattern: Dict) -> float:
        """
        패턴의 가중치를 계산합니다.

        Args:
            pattern: 분석된 패턴

        Returns:
            float: 패턴의 가중치 (0.0 ~ 1.0)
        """
        base_weight = 0.5

        if pattern["type"] == "metric_based":
            # 이상치 비율에 따른 가중치 조정
            anomaly_ratio = pattern["anomaly_count"] / self.frequency_threshold
            severity_factor = min(anomaly_ratio * 2, 1.0)
            base_weight += severity_factor * 0.3

            # 값의 변동성에 따른 가중치 조정
            value_range = pattern["max_value"] - pattern["min_value"]
            if value_range > 0:
                variation_factor = min(value_range / pattern["avg_value"], 1.0)
                base_weight += variation_factor * 0.2

        elif pattern["type"] == "time_based":
            # 발생 빈도에 따른 가중치 조정
            frequency_factor = min(pattern["count"] / (self.frequency_threshold * 2), 1.0)
            base_weight += frequency_factor * 0.3

        elif pattern["type"] == "type_based":
            # 심각도와 발생 빈도에 따른 가중치 조정
            severity_bonus = {
                FeedbackSeverity.CRITICAL: 0.3,
                FeedbackSeverity.HIGH: 0.2,
                FeedbackSeverity.MEDIUM: 0.1,
                FeedbackSeverity.LOW: 0.0
            }.get(pattern["main_severity"], 0.0)

            frequency_factor = min(pattern["count"] / (self.frequency_threshold * 2), 1.0)
            base_weight += severity_bonus + (frequency_factor * 0.2)

        return min(base_weight, 1.0)

    def get_significant_patterns(self, patterns: List[Dict], threshold: float = 0.7) -> List[Dict]:
        """
        중요도가 높은 패턴들을 필터링합니다.

        Args:
            patterns: 분석된 패턴 목록
            threshold: 중요도 임계값 (기본값: 0.7)

        Returns:
            List[Dict]: 중요도가 높은 패턴 목록
        """
        significant_patterns = []

        for pattern in patterns:
            weight = self._calculate_pattern_weight(pattern)
            if weight >= threshold:
                pattern["weight"] = weight
                significant_patterns.append(pattern)

        return sorted(significant_patterns, key=lambda x: x["weight"], reverse=True)

    def suggest_improvement_type(self, pattern: Dict) -> Tuple[ImprovementType, float]:
        """
        패턴을 기반으로 개선사항 유형을 제안합니다.

        Args:
            pattern: 발견된 패턴

        Returns:
            Tuple[ImprovementType, float]: (제안된 개선사항 유형, 신뢰도)
        """
        if pattern["type"] == "metric_based":
            # 메트릭 기반 패턴은 주로 성능이나 리소스 관련
            if "cpu" in pattern["metric_name"].lower() or "memory" in pattern["metric_name"].lower():
                return ImprovementType.RESOURCE, 0.8
            elif "time" in pattern["metric_name"].lower() or "duration" in pattern["metric_name"].lower():
                return ImprovementType.PERFORMANCE, 0.8

        elif pattern["type"] == "type_based":
            # 피드백 유형 기반 매핑
            type_mapping = {
                FeedbackType.PERFORMANCE: (ImprovementType.PERFORMANCE, 0.9),
                FeedbackType.RESOURCE: (ImprovementType.RESOURCE, 0.9),
                FeedbackType.ERROR: (ImprovementType.RELIABILITY, 0.8),
                FeedbackType.SUGGESTION: (ImprovementType.STRATEGY, 0.7)
            }
            if pattern["feedback_type"] in type_mapping:
                return type_mapping[pattern["feedback_type"]]

        # 기본값
        return ImprovementType.EFFICIENCY, 0.5

    def calculate_pattern_significance(self, pattern: Dict) -> float:
        """
        패턴의 중요도를 계산합니다.

        Args:
            pattern: 발견된 패턴

        Returns:
            float: 패턴의 중요도 (0.0 ~ 1.0)
        """
        base_score = 0.5

        if pattern["type"] == "metric_based":
            # 이상치가 많을수록 중요도 증가
            anomaly_factor = min(pattern["anomaly_count"] / self.frequency_threshold, 1.0)
            base_score += anomaly_factor * 0.3

        elif pattern["type"] == "type_based":
            # 발생 빈도와 심각도 기반 중요도 계산
            frequency_factor = min(pattern["count"] / (self.frequency_threshold * 2), 1.0)
            severity_bonus = {
                FeedbackSeverity.CRITICAL: 0.3,
                FeedbackSeverity.HIGH: 0.2,
                FeedbackSeverity.MEDIUM: 0.1
            }.get(pattern["main_severity"], 0.0)
            base_score += frequency_factor * 0.2 + severity_bonus

        elif pattern["type"] == "time_based":
            # 발생 빈도 기반 중요도 계산
            frequency_factor = min(pattern["count"] / (self.frequency_threshold * 2), 1.0)
            base_score += frequency_factor * 0.2

        return min(max(base_score, 0.0), 1.0)  # 0.0 ~ 1.0 범위로 제한
