"""
피드백 데이터 모델에 대한 테스트를 구현하는 모듈입니다.
"""

import pytest
from datetime import datetime
from typing import Dict

from app.feedback.models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    FeedbackStatus
)

def test_feedback_type_enum():
    """FeedbackType 열거형 테스트"""
    assert FeedbackType.EXECUTION == "execution"
    assert FeedbackType.PERFORMANCE == "performance"
    assert FeedbackType.USABILITY == "usability"
    assert FeedbackType.ERROR == "error"
    assert FeedbackType.SUGGESTION == "suggestion"
    assert FeedbackType.OTHER == "other"

def test_feedback_severity_enum():
    """FeedbackSeverity 열거형 테스트"""
    assert FeedbackSeverity.LOW == "low"
    assert FeedbackSeverity.MEDIUM == "medium"
    assert FeedbackSeverity.HIGH == "high"
    assert FeedbackSeverity.CRITICAL == "critical"

def test_feedback_status_enum():
    """FeedbackStatus 열거형 테스트"""
    assert FeedbackStatus.NEW == "new"
    assert FeedbackStatus.IN_REVIEW == "in_review"
    assert FeedbackStatus.ACCEPTED == "accepted"
    assert FeedbackStatus.REJECTED == "rejected"
    assert FeedbackStatus.IMPLEMENTED == "implemented"
    assert FeedbackStatus.CLOSED == "closed"

def test_feedback_creation(sample_feedback_data):
    """Feedback 객체 생성 테스트"""
    feedback = Feedback(**sample_feedback_data)

    assert feedback.id == sample_feedback_data["id"]
    assert feedback.plan_id == sample_feedback_data["plan_id"]
    assert feedback.type == sample_feedback_data["type"]
    assert feedback.severity == sample_feedback_data["severity"]
    assert feedback.title == sample_feedback_data["title"]
    assert feedback.description == sample_feedback_data["description"]
    assert feedback.step_index == sample_feedback_data["step_index"]
    assert feedback.metrics == sample_feedback_data["metrics"]
    assert feedback.tags == sample_feedback_data["tags"]
    assert feedback.status == FeedbackStatus.NEW

def test_feedback_status_update(sample_feedback):
    """피드백 상태 업데이트 테스트"""
    original_updated_at = sample_feedback.updated_at

    # 상태 업데이트
    sample_feedback.update_status(FeedbackStatus.IN_REVIEW)
    assert sample_feedback.status == FeedbackStatus.IN_REVIEW
    assert sample_feedback.updated_at > original_updated_at

def test_feedback_metric_addition(sample_feedback):
    """피드백 메트릭 추가 테스트"""
    original_updated_at = sample_feedback.updated_at

    # 새로운 메트릭 추가
    sample_feedback.add_metric("cpu_usage", 75.5)
    assert sample_feedback.metrics["cpu_usage"] == 75.5
    assert sample_feedback.updated_at > original_updated_at

def test_feedback_tag_addition(sample_feedback):
    """피드백 태그 추가 테스트"""
    original_updated_at = sample_feedback.updated_at
    original_tags_count = len(sample_feedback.tags)

    # 새로운 태그 추가
    sample_feedback.add_tag("new_tag")
    assert "new_tag" in sample_feedback.tags
    assert len(sample_feedback.tags) == original_tags_count + 1
    assert sample_feedback.updated_at > original_updated_at

    # 중복 태그 추가 시도
    sample_feedback.add_tag("new_tag")
    assert len(sample_feedback.tags) == original_tags_count + 1  # 변화 없음

def test_feedback_to_dict(sample_feedback):
    """피드백 딕셔너리 변환 테스트"""
    feedback_dict = sample_feedback.to_dict()

    assert isinstance(feedback_dict, dict)
    assert feedback_dict["id"] == sample_feedback.id
    assert feedback_dict["plan_id"] == sample_feedback.plan_id
    assert feedback_dict["type"] == sample_feedback.type.value
    assert feedback_dict["severity"] == sample_feedback.severity.value
    assert feedback_dict["status"] == sample_feedback.status.value
    assert feedback_dict["title"] == sample_feedback.title
    assert feedback_dict["description"] == sample_feedback.description
    assert isinstance(feedback_dict["created_at"], str)
    assert isinstance(feedback_dict["updated_at"], str)
    assert feedback_dict["step_index"] == sample_feedback.step_index
    assert feedback_dict["metrics"] == sample_feedback.metrics
    assert feedback_dict["tags"] == sample_feedback.tags

def test_feedback_validation():
    """피드백 데이터 유효성 검증 테스트"""
    # 필수 필드 누락
    with pytest.raises(ValueError):
        Feedback()

    # 잘못된 타입의 데이터
    with pytest.raises(ValueError):
        Feedback(
            id="test-001",
            plan_id="plan-001",
            type="invalid_type",  # 잘못된 타입
            severity=FeedbackSeverity.MEDIUM,
            title="Test",
            description="Test description"
        )

    # 잘못된 심각도
    with pytest.raises(ValueError):
        Feedback(
            id="test-001",
            plan_id="plan-001",
            type=FeedbackType.EXECUTION,
            severity="invalid_severity",  # 잘못된 심각도
            title="Test",
            description="Test description"
        )
