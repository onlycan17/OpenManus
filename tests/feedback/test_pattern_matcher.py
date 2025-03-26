"""
PatternMatcher 클래스의 테스트를 정의하는 모듈입니다.
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from app.feedback.models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    ImprovementType
)
from app.feedback.pattern_matcher import PatternMatcher

@pytest.fixture
def pattern_matcher():
    """PatternMatcher 인스턴스를 생성합니다."""
    return PatternMatcher()

@pytest.fixture
def sample_feedbacks():
    """테스트용 피드백 목록을 생성합니다."""
    now = datetime.now()
    feedbacks = []

    # 시간 기반 패턴을 위한 피드백
    for i in range(5):  # 특정 시간대(10시)에 집중된 피드백
        feedbacks.append(Feedback(
            id=f"fb-time-{i}",
            plan_id="plan-1",
            type=FeedbackType.PERFORMANCE,
            severity=FeedbackSeverity.MEDIUM,
            title=f"Performance Issue {i}",
            description="Performance degradation detected",
            created_at=now.replace(hour=10, minute=i*10)
        ))

    # 유형 기반 패턴을 위한 피드백
    for i in range(4):  # ERROR 유형 피드백 집중
        feedbacks.append(Feedback(
            id=f"fb-type-{i}",
            plan_id="plan-1",
            type=FeedbackType.ERROR,
            severity=FeedbackSeverity.HIGH,
            title=f"Error {i}",
            description="Error occurred during execution",
            created_at=now - timedelta(hours=i)
        ))

    # 메트릭 기반 패턴을 위한 피드백
    for i in range(3):  # CPU 사용량 이상치
        feedback = Feedback(
            id=f"fb-metric-{i}",
            plan_id="plan-1",
            type=FeedbackType.PERFORMANCE,
            severity=FeedbackSeverity.HIGH,
            title=f"High CPU Usage {i}",
            description="CPU usage exceeded threshold",
            created_at=now - timedelta(hours=i*2)
        )
        feedback.add_metric("cpu_usage", 90 + i)  # 높은 CPU 사용량
        feedbacks.append(feedback)

    return feedbacks

def test_pattern_matcher_initialization(pattern_matcher):
    """PatternMatcher 초기화를 테스트합니다."""
    assert isinstance(pattern_matcher, PatternMatcher)
    assert pattern_matcher.frequency_threshold == 3
    assert pattern_matcher.similarity_threshold == 0.7
    assert isinstance(pattern_matcher.time_window, timedelta)

def test_find_time_based_patterns(pattern_matcher, sample_feedbacks):
    """시간 기반 패턴 분석을 테스트합니다."""
    patterns = pattern_matcher._find_time_based_patterns(sample_feedbacks)

    assert len(patterns) > 0
    pattern = patterns[0]
    assert pattern["type"] == "time_based"
    assert pattern["hour"] == 10  # 10시대 피드백 집중
    assert pattern["count"] >= 5
    assert "description" in pattern

def test_find_type_based_patterns(pattern_matcher, sample_feedbacks):
    """유형 기반 패턴 분석을 테스트합니다."""
    patterns = pattern_matcher._find_type_based_patterns(sample_feedbacks)

    assert len(patterns) > 0
    pattern = next(p for p in patterns if p["feedback_type"] == FeedbackType.ERROR)
    assert pattern["type"] == "type_based"
    assert pattern["count"] >= 4
    assert pattern["main_severity"] == FeedbackSeverity.HIGH
    assert "description" in pattern

def test_find_metric_based_patterns(pattern_matcher, sample_feedbacks):
    """메트릭 기반 패턴 분석을 테스트합니다."""
    patterns = pattern_matcher._find_metric_based_patterns(sample_feedbacks)

    assert len(patterns) > 0
    pattern = next(p for p in patterns if p["metric_name"] == "cpu_usage")
    assert pattern["type"] == "metric_based"
    assert pattern["anomaly_count"] > 0
    assert "avg_value" in pattern
    assert "description" in pattern

def test_find_patterns_integration(pattern_matcher, sample_feedbacks):
    """전체 패턴 분석 통합 테스트를 수행합니다."""
    patterns = pattern_matcher.find_patterns(sample_feedbacks)

    assert len(patterns) > 0
    pattern_types = {p["type"] for p in patterns}
    assert "time_based" in pattern_types
    assert "type_based" in pattern_types
    assert "metric_based" in pattern_types

def test_suggest_improvement_type(pattern_matcher):
    """개선사항 유형 제안을 테스트합니다."""
    # 메트릭 기반 패턴
    metric_pattern = {
        "type": "metric_based",
        "metric_name": "cpu_usage",
        "anomaly_count": 3,
        "avg_value": 92.0
    }
    imp_type, confidence = pattern_matcher.suggest_improvement_type(metric_pattern)
    assert imp_type == ImprovementType.RESOURCE
    assert confidence >= 0.7

    # 유형 기반 패턴
    type_pattern = {
        "type": "type_based",
        "feedback_type": FeedbackType.PERFORMANCE,
        "count": 5,
        "main_severity": FeedbackSeverity.HIGH
    }
    imp_type, confidence = pattern_matcher.suggest_improvement_type(type_pattern)
    assert imp_type == ImprovementType.PERFORMANCE
    assert confidence >= 0.7

def test_calculate_pattern_significance(pattern_matcher):
    """패턴 중요도 계산을 테스트합니다."""
    # 메트릭 기반 패턴
    metric_pattern = {
        "type": "metric_based",
        "metric_name": "cpu_usage",
        "anomaly_count": 5,
        "avg_value": 95.0
    }
    significance = pattern_matcher.calculate_pattern_significance(metric_pattern)
    assert 0 <= significance <= 1
    assert significance > 0.5  # 높은 이상치 수로 인한 높은 중요도

    # 유형 기반 패턴
    type_pattern = {
        "type": "type_based",
        "feedback_type": FeedbackType.ERROR,
        "count": 10,
        "main_severity": FeedbackSeverity.CRITICAL
    }
    significance = pattern_matcher.calculate_pattern_significance(type_pattern)
    assert 0 <= significance <= 1
    assert significance > 0.7  # 심각도와 빈도가 높아 높은 중요도
