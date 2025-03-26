"""
ResultTracker 클래스의 테스트를 정의하는 모듈입니다.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

from app.feedback.models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    ImprovementType,
    ImprovementSuggestion,
    ImprovementStatus
)
from app.feedback.result_tracker import ResultTracker

@pytest.fixture
def result_tracker():
    """ResultTracker 인스턴스를 생성합니다."""
    return ResultTracker()

@pytest.fixture
def sample_suggestion():
    """테스트용 개선사항을 생성합니다."""
    return ImprovementSuggestion(
        id="imp-test",
        type=ImprovementType.PERFORMANCE,
        title="Performance Improvement",
        description="Improve system performance",
        priority=0.7
    )

@pytest.fixture
def sample_metrics():
    """테스트용 메트릭을 생성합니다."""
    return {
        "before": {
            "response_time": 500,  # ms
            "cpu_usage": 80,       # %
            "memory_usage": 70,    # %
            "error_rate": 5        # %
        },
        "after": {
            "response_time": 300,  # ms
            "cpu_usage": 60,       # %
            "memory_usage": 50,    # %
            "error_rate": 2        # %
        }
    }

@pytest.fixture
def sample_feedbacks():
    """테스트용 피드백 목록을 생성합니다."""
    now = datetime.now()
    feedbacks = []

    # 구현 전 피드백 (부정적)
    for i in range(5):
        feedbacks.append(Feedback(
            id=f"fb-before-{i}",
            plan_id="plan-1",
            type=FeedbackType.PERFORMANCE,
            severity=FeedbackSeverity.HIGH,
            title=f"Performance Issue {i}",
            description="Poor performance detected",
            created_at=now - timedelta(days=10+i)
        ))

    # 구현 후 피드백 (긍정적)
    for i in range(3):
        feedbacks.append(Feedback(
            id=f"fb-after-{i}",
            plan_id="plan-1",
            type=FeedbackType.PERFORMANCE,
            severity=FeedbackSeverity.LOW,
            title=f"Performance Feedback {i}",
            description="Performance has improved",
            created_at=now - timedelta(hours=i)
        ))

    return feedbacks

def test_result_tracker_initialization(result_tracker):
    """ResultTracker 초기화를 테스트합니다."""
    assert isinstance(result_tracker, ResultTracker)
    assert isinstance(result_tracker.tracking_window, timedelta)
    assert 0 < result_tracker.success_threshold < 1

def test_track_implementation(result_tracker, sample_suggestion, sample_metrics):
    """구현 결과 추적을 테스트합니다."""
    result = result_tracker.track_implementation(
        sample_suggestion,
        sample_metrics["before"],
        sample_metrics["after"]
    )

    assert "suggestion_id" in result
    assert "improvements" in result
    assert "overall_score" in result
    assert "success" in result

    # 개선율 확인
    improvements = result["improvements"]
    assert all(imp["improvement_rate"] > 0 for imp in improvements.values())
    assert result["overall_score"] > 0.5  # 전반적인 개선이 있으므로
    assert result["success"]  # 성공 임계값을 넘어섬

def test_track_feedback_changes(result_tracker, sample_suggestion, sample_feedbacks):
    """피드백 변화 추적을 테스트합니다."""
    result = result_tracker.track_feedback_changes(sample_suggestion, sample_feedbacks)

    assert "total_feedbacks" in result
    assert "type_distribution" in result
    assert "severity_distribution" in result
    assert "daily_counts" in result
    assert "trend" in result

    # 분포 확인
    assert result["total_feedbacks"] == len(sample_feedbacks)
    assert FeedbackType.PERFORMANCE.value in result["type_distribution"]
    assert FeedbackSeverity.HIGH.value in result["severity_distribution"]

    # 트렌드 확인
    trend = result["trend"]
    assert "direction" in trend
    assert "slope" in trend
    assert "confidence" in trend

def test_evaluate_success(result_tracker, sample_suggestion):
    """성공 여부 평가를 테스트합니다."""
    implementation_result = {
        "success": True,
        "overall_score": 0.8,
        "improvements": {
            "response_time": {"improvement_rate": 0.4},
            "cpu_usage": {"improvement_rate": 0.25}
        }
    }

    feedback_changes = {
        "trend": {"direction": "decreasing", "slope": -0.5, "confidence": 0.8},
        "severity_distribution": {
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 5
        }
    }

    is_successful, confidence, description = result_tracker.evaluate_success(
        sample_suggestion,
        implementation_result,
        feedback_changes
    )

    assert isinstance(is_successful, bool)
    assert 0 <= confidence <= 1
    assert isinstance(description, str)
    assert is_successful  # 긍정적인 결과이므로 성공으로 판단

def test_get_metrics_history(result_tracker, sample_suggestion, sample_metrics):
    """메트릭 이력 조회를 테스트합니다."""
    # 메트릭 이력 생성
    result_tracker.track_implementation(
        sample_suggestion,
        sample_metrics["before"],
        sample_metrics["after"]
    )

    # 전체 메트릭 이력 조회
    history = result_tracker.get_metrics_history(sample_suggestion.id)
    assert len(history) > 0
    assert all("timestamp" in entry for entry in history)
    assert all("metrics" in entry for entry in history)

    # 특정 메트릭 이력 조회
    cpu_history = result_tracker.get_metrics_history(sample_suggestion.id, "cpu_usage")
    assert len(cpu_history) > 0
    assert all("cpu_usage" in entry for entry in cpu_history)

def test_get_feedback_history(result_tracker, sample_suggestion, sample_feedbacks):
    """피드백 이력 조회를 테스트합니다."""
    # 피드백 이력 생성
    result_tracker.track_feedback_changes(sample_suggestion, sample_feedbacks)

    # 전체 피드백 이력 조회
    history = result_tracker.get_feedback_history(sample_suggestion.id)
    assert len(history) == len(sample_feedbacks)

    # 특정 유형의 피드백 이력 조회
    performance_history = result_tracker.get_feedback_history(
        sample_suggestion.id,
        FeedbackType.PERFORMANCE
    )
    assert len(performance_history) > 0
    assert all(f.type == FeedbackType.PERFORMANCE for f in performance_history)

def test_analyze_feedback_trend(result_tracker):
    """피드백 트렌드 분석을 테스트합니다."""
    now = datetime.now()
    feedbacks = []

    # 감소하는 트렌드 생성
    for i in range(7):
        count = 5 - i  # 점차 감소하는 피드백 수
        for j in range(count):
            feedbacks.append(Feedback(
                id=f"fb-{i}-{j}",
                plan_id="plan-1",
                type=FeedbackType.PERFORMANCE,
                severity=FeedbackSeverity.MEDIUM,
                title=f"Feedback {i}-{j}",
                description="Test feedback",
                created_at=now - timedelta(days=i)
            ))

    trend = result_tracker._analyze_feedback_trend(feedbacks)
    assert trend["direction"] == "decreasing"
    assert trend["slope"] < 0
    assert 0 < trend["confidence"] <= 1

def test_calculate_overall_score(result_tracker):
    """전체 개선 점수 계산을 테스트합니다."""
    improvements = {
        "response_time": {
            "before": 500,
            "after": 300,
            "improvement_rate": 0.4
        },
        "cpu_usage": {
            "before": 80,
            "after": 60,
            "improvement_rate": 0.25
        },
        "memory_usage": {
            "before": 70,
            "after": 50,
            "improvement_rate": 0.29
        }
    }

    score = result_tracker._calculate_overall_score(improvements)
    assert 0 <= score <= 1

    # 성능 관련 메트릭이 더 높은 가중치를 가지는지 확인
    performance_improvements = {
        "response_time": improvements["response_time"]
    }
    performance_score = result_tracker._calculate_overall_score(performance_improvements)
    assert performance_score > 0
