"""
ImprovementSuggester 클래스의 테스트를 정의하는 모듈입니다.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

from app.feedback.models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    ImprovementType,
    ImprovementStatus,
    ImprovementSuggestion
)
from app.feedback.suggester import ImprovementSuggester

@pytest.fixture
def suggester():
    """ImprovementSuggester 인스턴스를 생성합니다."""
    return ImprovementSuggester()

@pytest.fixture
def sample_feedbacks():
    """테스트용 피드백 목록을 생성합니다."""
    now = datetime.now()
    feedbacks = []

    # 성능 관련 피드백
    for i in range(5):
        feedback = Feedback(
            id=f"fb-perf-{i}",
            plan_id="plan-1",
            type=FeedbackType.PERFORMANCE,
            severity=FeedbackSeverity.HIGH,
            title=f"Performance Issue {i}",
            description="Performance degradation detected",
            created_at=now - timedelta(hours=i)
        )
        feedback.add_metric("response_time", 500 + i * 50)
        feedback.add_metric("cpu_usage", 80 + i * 2)
        feedbacks.append(feedback)

    # 에러 관련 피드백
    for i in range(3):
        feedback = Feedback(
            id=f"fb-err-{i}",
            plan_id="plan-1",
            type=FeedbackType.ERROR,
            severity=FeedbackSeverity.CRITICAL,
            title=f"Error {i}",
            description="Critical error occurred",
            created_at=now - timedelta(hours=i*2)
        )
        feedback.add_metric("error_count", 10 + i)
        feedbacks.append(feedback)

    return feedbacks

@pytest.fixture
def sample_metrics():
    """테스트용 메트릭을 생성합니다."""
    return {
        "before": {
            "response_time": 500,
            "cpu_usage": 80,
            "error_count": 10
        },
        "after": {
            "response_time": 300,
            "cpu_usage": 60,
            "error_count": 2
        }
    }

def test_suggester_initialization(suggester):
    """ImprovementSuggester 초기화를 테스트합니다."""
    assert isinstance(suggester, ImprovementSuggester)
    assert suggester.pattern_matcher is not None
    assert suggester.priority_manager is not None
    assert suggester.result_tracker is not None

def test_analyze_feedbacks(suggester, sample_feedbacks):
    """피드백 분석 및 개선사항 제안을 테스트합니다."""
    suggestions = suggester.analyze_feedbacks(sample_feedbacks)

    assert len(suggestions) > 0

    # 제안된 개선사항 검증
    for suggestion in suggestions:
        assert isinstance(suggestion, ImprovementSuggestion)
        assert suggestion.id.startswith("imp-")
        assert suggestion.type in ImprovementType
        assert 0 <= suggestion.priority <= 1
        assert len(suggestion.related_feedbacks) > 0
        assert suggestion.status == ImprovementStatus.PROPOSED

def test_get_suggestion(suggester, sample_feedbacks):
    """개선사항 조회를 테스트합니다."""
    suggestions = suggester.analyze_feedbacks(sample_feedbacks)
    suggestion_id = suggestions[0].id

    # 존재하는 개선사항 조회
    suggestion = suggester.get_suggestion(suggestion_id)
    assert suggestion is not None
    assert suggestion.id == suggestion_id

    # 존재하지 않는 개선사항 조회
    non_existent = suggester.get_suggestion("non-existent")
    assert non_existent is None

def test_get_all_suggestions(suggester, sample_feedbacks):
    """모든 개선사항 조회를 테스트합니다."""
    suggestions = suggester.analyze_feedbacks(sample_feedbacks)

    # 전체 개선사항 조회
    all_suggestions = suggester.get_all_suggestions()
    assert len(all_suggestions) == len(suggestions)

    # 특정 상태의 개선사항 조회
    proposed = suggester.get_all_suggestions(ImprovementStatus.PROPOSED)
    assert len(proposed) == len(suggestions)
    assert all(s.status == ImprovementStatus.PROPOSED for s in proposed)

def test_update_suggestion_status(suggester, sample_feedbacks):
    """개선사항 상태 업데이트를 테스트합니다."""
    suggestions = suggester.analyze_feedbacks(sample_feedbacks)
    suggestion_id = suggestions[0].id

    # 상태 업데이트
    success = suggester.update_suggestion_status(
        suggestion_id,
        ImprovementStatus.IMPLEMENTING
    )
    assert success

    # 업데이트된 상태 확인
    suggestion = suggester.get_suggestion(suggestion_id)
    assert suggestion.status == ImprovementStatus.IMPLEMENTING

    # 존재하지 않는 개선사항 업데이트
    success = suggester.update_suggestion_status(
        "non-existent",
        ImprovementStatus.IMPLEMENTING
    )
    assert not success

def test_track_implementation_result(suggester, sample_feedbacks, sample_metrics):
    """구현 결과 추적을 테스트합니다."""
    suggestions = suggester.analyze_feedbacks(sample_feedbacks)
    suggestion = suggestions[0]

    # 새로운 피드백 생성
    now = datetime.now()
    new_feedbacks = [
        Feedback(
            id="fb-new-1",
            plan_id="plan-1",
            type=FeedbackType.PERFORMANCE,
            severity=FeedbackSeverity.LOW,
            title="Improved Performance",
            description="Performance has improved",
            created_at=now
        )
    ]

    # 구현 결과 추적
    result = suggester.track_implementation_result(
        suggestion.id,
        sample_metrics["before"],
        sample_metrics["after"],
        new_feedbacks
    )

    assert "suggestion_id" in result
    assert "implementation_result" in result
    assert "feedback_changes" in result
    assert "evaluation" in result

    evaluation = result["evaluation"]
    assert "success" in evaluation
    assert "confidence" in evaluation
    assert "description" in evaluation

def test_get_implementation_history(suggester, sample_feedbacks, sample_metrics):
    """구현 이력 조회를 테스트합니다."""
    suggestions = suggester.analyze_feedbacks(sample_feedbacks)
    suggestion = suggestions[0]

    # 구현 결과 기록
    suggester.track_implementation_result(
        suggestion.id,
        sample_metrics["before"],
        sample_metrics["after"],
        sample_feedbacks[:2]  # 일부 피드백만 사용
    )

    # 이력 조회
    metrics_history, feedback_history = suggester.get_implementation_history(suggestion.id)

    assert len(metrics_history) > 0
    assert len(feedback_history) > 0
    assert all("timestamp" in entry for entry in metrics_history)
    assert all("metrics" in entry for entry in metrics_history)
    assert all(isinstance(f, Feedback) for f in feedback_history)

def test_create_suggestion(suggester):
    """개선사항 생성을 테스트합니다."""
    pattern = {
        "type": "metric_based",
        "metric_name": "response_time",
        "anomaly_count": 5,
        "avg_value": 500,
        "description": "High response time detected"
    }

    suggestion = suggester._create_suggestion(
        improvement_type=ImprovementType.PERFORMANCE,
        pattern=pattern,
        confidence=0.8,
        significance=0.7,
        related_feedbacks=["fb-1", "fb-2"]
    )

    assert isinstance(suggestion, ImprovementSuggestion)
    assert suggestion.type == ImprovementType.PERFORMANCE
    assert suggestion.priority == 0.7
    assert len(suggestion.related_feedbacks) == 2
    assert "performance" in suggestion.tags
    assert "metric_based" in suggestion.tags
    assert suggestion.expected_benefits["confidence"] == 0.8
    assert suggestion.expected_benefits["significance"] == 0.7

def test_integration(suggester, sample_feedbacks, sample_metrics):
    """통합 기능을 테스트합니다."""
    # 1. 피드백 분석 및 개선사항 제안
    suggestions = suggester.analyze_feedbacks(sample_feedbacks)
    assert len(suggestions) > 0
    suggestion = suggestions[0]

    # 2. 상태 업데이트
    suggester.update_suggestion_status(suggestion.id, ImprovementStatus.IMPLEMENTING)
    assert suggestion.status == ImprovementStatus.IMPLEMENTING

    # 3. 구현 결과 추적
    result = suggester.track_implementation_result(
        suggestion.id,
        sample_metrics["before"],
        sample_metrics["after"],
        sample_feedbacks[:2]
    )
    assert result["evaluation"]["success"]

    # 4. 이력 조회
    metrics_history, feedback_history = suggester.get_implementation_history(suggestion.id)
    assert len(metrics_history) > 0
    assert len(feedback_history) > 0

    # 5. 최종 상태 업데이트
    suggester.update_suggestion_status(suggestion.id, ImprovementStatus.IMPLEMENTED)
    assert suggestion.status == ImprovementStatus.IMPLEMENTED
