"""
개선사항의 우선순위를 관리하는 모듈입니다.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from functools import lru_cache
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from .models import (
    Feedback,
    FeedbackSeverity,
    ImprovementSuggestion,
    ImprovementType
)

class PriorityManager:
    """
    개선사항의 우선순위를 계산하고 관리하는 클래스입니다.
    병렬 처리와 캐싱을 통해 성능을 최적화합니다.
    """

    def __init__(self):
        """PriorityManager 객체를 초기화합니다."""
        # 우선순위 계산을 위한 가중치 설정
        self.weights = {
            "severity": 0.35,  # 심각도 가중치
            "frequency": 0.25,  # 발생 빈도 가중치
            "impact": 0.20,    # 영향도 가중치
            "cost": 0.10,      # 구현 비용 가중치
            "urgency": 0.10    # 긴급도 가중치
        }

        # 유형별 기본 우선순위 점수
        self.type_base_scores = {
            ImprovementType.PERFORMANCE: 0.8,
            ImprovementType.RELIABILITY: 0.9,
            ImprovementType.RESOURCE: 0.7,
            ImprovementType.EFFICIENCY: 0.6,
            ImprovementType.STRATEGY: 0.5
        }

        # 병렬 처리를 위한 설정
        self.max_workers = mp.cpu_count()
        self._priority_cache = {}

    def _generate_cache_key(self, suggestion: ImprovementSuggestion, feedbacks: List[Feedback]) -> str:
        """캐시 키를 생성합니다."""
        feedback_keys = [f.id for f in sorted(feedbacks, key=lambda x: x.id)]
        return f"{suggestion.id}|{','.join(feedback_keys)}"

    @lru_cache(maxsize=128)
    def calculate_priority(
        self,
        suggestion: ImprovementSuggestion,
        related_feedbacks: Tuple[Feedback, ...]  # 캐시를 위해 튜플 사용
    ) -> float:
        """
        개선사항의 우선순위를 계산합니다.

        Args:
            suggestion: 우선순위를 계산할 개선사항
            related_feedbacks: 관련된 피드백 목록 (튜플)

        Returns:
            float: 계산된 우선순위 (0.0 ~ 1.0)
        """
        # 기본 점수 (유형 기반)
        base_score = self.type_base_scores.get(suggestion.type, 0.5)

        # 병렬로 각 점수 계산
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_severity = executor.submit(self._calculate_severity_score, related_feedbacks)
            future_frequency = executor.submit(self._calculate_frequency_score, related_feedbacks)
            future_impact = executor.submit(self._calculate_impact_score, suggestion)
            future_cost = executor.submit(self._calculate_cost_score, suggestion)
            future_urgency = executor.submit(self._calculate_urgency_score, related_feedbacks)

            # 결과 수집
            severity_score = future_severity.result()
            frequency_score = future_frequency.result()
            impact_score = future_impact.result()
            cost_score = future_cost.result()
            urgency_score = future_urgency.result()

        # 최종 우선순위 계산 (넘파이 사용)
        scores = np.array([severity_score, frequency_score, impact_score, cost_score, urgency_score])
        weights = np.array([self.weights[w] for w in ["severity", "frequency", "impact", "cost", "urgency"]])
        weighted_sum = np.sum(scores * weights)

        priority = (base_score + weighted_sum) / 2
        return float(np.clip(priority, 0.0, 1.0))

    @lru_cache(maxsize=128)
    def _calculate_severity_score(self, feedbacks: Tuple[Feedback, ...]) -> float:
        """심각도 점수를 계산합니다."""
        if not feedbacks:
            return 0.0

        # 심각도별 가중치 (넘파이 배열)
        severity_weights = np.array([
            1.0,  # CRITICAL
            0.8,  # HIGH
            0.5,  # MEDIUM
            0.2   # LOW
        ])

        # 심각도 인덱스 배열 생성
        severity_indices = np.array([feedback.severity.value for feedback in feedbacks])

        # 가중 평균 계산
        weighted_sum = np.sum(severity_weights[severity_indices])
        return float(weighted_sum / len(feedbacks))

    @lru_cache(maxsize=128)
    def _calculate_frequency_score(self, feedbacks: Tuple[Feedback, ...]) -> float:
        """발생 빈도 점수를 계산합니다."""
        if not feedbacks:
            return 0.0

        # 최근 일주일 내 피드백 수 확인
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        # 넘파이 배열로 변환하여 계산
        timestamps = np.array([f.created_at.timestamp() for f in feedbacks])
        week_ago_ts = week_ago.timestamp()
        recent_count = np.sum(timestamps >= week_ago_ts)

        # 일일 평균 발생 빈도 계산
        daily_avg = recent_count / 7.0
        return float(np.clip(daily_avg / 5.0, 0.0, 1.0))

    @lru_cache(maxsize=128)
    def _calculate_impact_score(self, suggestion: ImprovementSuggestion) -> float:
        """영향도 점수를 계산합니다."""
        if not suggestion.expected_benefits:
            return 0.5  # 기본값

        # 영향도 가중치 (넘파이 배열)
        impact_weights = np.array([0.4, 0.3, 0.3])
        impact_values = np.array([
            suggestion.expected_benefits.get("performance_improvement", 0.0),
            suggestion.expected_benefits.get("resource_saving", 0.0),
            suggestion.expected_benefits.get("reliability_improvement", 0.0)
        ])

        impact_score = float(np.sum(impact_values * impact_weights))
        return float(np.clip(impact_score, 0.0, 1.0))

    @lru_cache(maxsize=128)
    def _calculate_cost_score(self, suggestion: ImprovementSuggestion) -> float:
        """구현 비용 점수를 계산합니다."""
        if not suggestion.implementation_cost:
            return 0.5  # 기본값

        # 비용 가중치 (넘파이 배열)
        cost_weights = np.array([0.4, 0.3, 0.3])
        cost_values = np.array([
            1 - suggestion.implementation_cost.get("development_time", 0.5),
            1 - suggestion.implementation_cost.get("resource_requirement", 0.5),
            1 - suggestion.implementation_cost.get("risk_level", 0.5)
        ])

        cost_score = float(np.sum(cost_values * cost_weights))
        return float(np.clip(cost_score, 0.0, 1.0))

    @lru_cache(maxsize=128)
    def _calculate_urgency_score(self, feedbacks: Tuple[Feedback, ...]) -> float:
        """긴급도 점수를 계산합니다."""
        if not feedbacks:
            return 0.0

        now = datetime.now()

        # 시간 차이와 심각도를 넘파이 배열로 변환
        time_diffs = np.array([(now - f.created_at).days for f in feedbacks])
        severity_values = np.array([f.severity.value for f in feedbacks])

        # 시간 가중치 계산 (7일 이내)
        time_weights = np.clip(1 - (time_diffs / 7), 0, 1)

        # 심각도 가중치
        severity_weights = np.array([0.2, 0.5, 0.8, 1.0])[severity_values]

        # 최종 점수 계산
        urgency_score = float(np.mean(time_weights * severity_weights))
        return float(np.clip(urgency_score, 0.0, 1.0))

    def sort_suggestions(
        self,
        suggestions: List[ImprovementSuggestion],
        feedbacks: Dict[str, List[Feedback]]
    ) -> List[ImprovementSuggestion]:
        """
        개선사항 목록을 우선순위에 따라 정렬합니다.
        병렬 처리를 통해 성능을 최적화합니다.

        Args:
            suggestions: 정렬할 개선사항 목록
            feedbacks: 개선사항별 관련 피드백 맵

        Returns:
            List[ImprovementSuggestion]: 우선순위로 정렬된 개선사항 목록
        """
        if not suggestions:
            return []

        # 병렬로 우선순위 계산
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_priorities = {
                suggestion: executor.submit(
                    self.calculate_priority,
                    suggestion,
                    tuple(feedbacks.get(suggestion.id, []))  # 튜플로 변환
                )
                for suggestion in suggestions
            }

            # 우선순위 결과 수집
            priorities = {
                suggestion: future.result()
                for suggestion, future in future_priorities.items()
            }

        # 우선순위에 따라 정렬
        return sorted(
            suggestions,
            key=lambda s: priorities[s],
            reverse=True
        )
