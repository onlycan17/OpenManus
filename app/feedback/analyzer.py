"""
피드백 분석 기능을 구현하는 모듈입니다.
이 모듈은 수집된 피드백을 분석하고 통계를 생성하는 기능을 제공합니다.
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

from app.feedback.models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    FeedbackStatus
)

class FeedbackAnalysis:
    """피드백 분석 결과를 담는 클래스"""

    def __init__(self):
        self.total_count: int = 0
        self.type_distribution: Dict[FeedbackType, int] = defaultdict(int)
        self.severity_distribution: Dict[FeedbackSeverity, int] = defaultdict(int)
        self.status_distribution: Dict[FeedbackStatus, int] = defaultdict(int)
        self.common_tags: List[Tuple[str, int]] = []
        self.metrics_summary: Dict[str, Dict[str, Union[int, float]]] = {}
        self.time_based_stats: Dict[str, int] = defaultdict(int)

class FeedbackAnalyzer:
    """피드백 분석기 클래스"""

    def analyze_feedbacks(
        self,
        feedbacks: List[Feedback],
        time_window: Optional[timedelta] = None
    ) -> FeedbackAnalysis:
        """피드백 분석 수행"""
        analysis = FeedbackAnalysis()

        # 시간 윈도우 적용
        if time_window:
            cutoff_time = datetime.now() - time_window
            feedbacks = [f for f in feedbacks if f.created_at >= cutoff_time]

        analysis.total_count = len(feedbacks)

        # 분포 분석
        for feedback in feedbacks:
            analysis.type_distribution[feedback.type] += 1
            analysis.severity_distribution[feedback.severity] += 1
            analysis.status_distribution[feedback.status] += 1

        # 태그 분석
        all_tags = []
        for feedback in feedbacks:
            all_tags.extend(feedback.tags)
        tag_counter = Counter(all_tags)
        analysis.common_tags = tag_counter.most_common()

        # 메트릭 분석
        metrics_data: Dict[str, List[Union[int, float]]] = defaultdict(list)
        for feedback in feedbacks:
            for key, value in feedback.metrics.items():
                if isinstance(value, (int, float)):
                    metrics_data[key].append(value)

        # 각 메트릭에 대한 통계 계산
        for key, values in metrics_data.items():
            if values:
                analysis.metrics_summary[key] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values)
                }

        # 시간 기반 통계
        for feedback in feedbacks:
            date_str = feedback.created_at.strftime("%Y-%m-%d")
            analysis.time_based_stats[date_str] += 1

        return analysis

    def get_critical_feedbacks(
        self,
        feedbacks: List[Feedback]
    ) -> List[Feedback]:
        """중요 피드백 추출"""
        return [
            feedback for feedback in feedbacks
            if feedback.severity == FeedbackSeverity.CRITICAL
        ]

    def get_trending_issues(
        self,
        feedbacks: List[Feedback],
        time_window: timedelta,
        min_occurrence: int = 2
    ) -> List[Tuple[str, int]]:
        """트렌드 이슈 분석"""
        cutoff_time = datetime.now() - time_window
        recent_feedbacks = [f for f in feedbacks if f.created_at >= cutoff_time]

        # 태그 기반 트렌드 분석
        tag_counter = Counter()
        for feedback in recent_feedbacks:
            tag_counter.update(feedback.tags)

        return [
            (tag, count) for tag, count in tag_counter.most_common()
            if count >= min_occurrence
        ]

    def get_performance_metrics(
        self,
        feedbacks: List[Feedback]
    ) -> Dict[str, Dict[str, Union[int, float]]]:
        """성능 메트릭 분석"""
        performance_feedbacks = [
            f for f in feedbacks
            if f.type == FeedbackType.PERFORMANCE
        ]

        metrics_data: Dict[str, List[Union[int, float]]] = defaultdict(list)
        for feedback in performance_feedbacks:
            for key, value in feedback.metrics.items():
                if isinstance(value, (int, float)):
                    metrics_data[key].append(value)

        metrics_summary = {}
        for key, values in metrics_data.items():
            if values:
                metrics_summary[key] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values)
                }

        return metrics_summary

    def get_feedback_summary(
        self,
        feedbacks: List[Feedback]
    ) -> Dict[str, Union[int, Dict]]:
        """피드백 요약 정보 생성"""
        total_count = len(feedbacks)
        if total_count == 0:
            return {"total_count": 0}

        type_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        status_counts = defaultdict(int)

        for feedback in feedbacks:
            type_counts[feedback.type.value] += 1
            severity_counts[feedback.severity.value] += 1
            status_counts[feedback.status.value] += 1

        return {
            "total_count": total_count,
            "type_distribution": dict(type_counts),
            "severity_distribution": dict(severity_counts),
            "status_distribution": dict(status_counts)
        }

    def get_resolution_rate(
        self,
        feedbacks: List[Feedback]
    ) -> float:
        """피드백 해결률 계산"""
        total = len(feedbacks)
        if total == 0:
            return 0.0

        resolved = sum(
            1 for f in feedbacks
            if f.status in [FeedbackStatus.IMPLEMENTED, FeedbackStatus.CLOSED]
        )

        return (resolved / total) * 100
