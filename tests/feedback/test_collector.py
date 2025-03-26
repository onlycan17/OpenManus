"""
피드백 수집기에 대한 테스트를 구현하는 모듈입니다.
"""

import pytest
from typing import Dict, List

from app.feedback.models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    FeedbackStatus
)
from app.feedback.collector import FeedbackCollector

def test_feedback_collector_initialization(feedback_collector):
    """FeedbackCollector 초기화 테스트"""
    assert isinstance(feedback_collector, FeedbackCollector)
    assert len(feedback_collector.get_all_feedbacks()) == 0

def test_create_feedback(feedback_collector, sample_feedback_data):
    """피드백 생성 테스트"""
    feedback = feedback_collector.create_feedback(
        plan_id=sample_feedback_data["plan_id"],
        type=sample_feedback_data["type"],
        severity=sample_feedback_data["severity"],
        title=sample_feedback_data["title"],
        description=sample_feedback_data["description"],
        step_index=sample_feedback_data["step_index"],
        metrics=sample_feedback_data["metrics"],
        tags=sample_feedback_data["tags"]
    )

    assert isinstance(feedback, Feedback)
    assert feedback.plan_id == sample_feedback_data["plan_id"]
    assert feedback.type == sample_feedback_data["type"]
    assert feedback.severity == sample_feedback_data["severity"]
    assert feedback.title == sample_feedback_data["title"]
    assert feedback.description == sample_feedback_data["description"]
    assert feedback.step_index == sample_feedback_data["step_index"]
    assert feedback.metrics == sample_feedback_data["metrics"]
    assert feedback.tags == sample_feedback_data["tags"]
    assert feedback.status == FeedbackStatus.NEW

def test_get_feedback(feedback_collector, sample_feedback_data):
    """피드백 조회 테스트"""
    feedback = feedback_collector.create_feedback(
        plan_id=sample_feedback_data["plan_id"],
        type=sample_feedback_data["type"],
        severity=sample_feedback_data["severity"],
        title=sample_feedback_data["title"],
        description=sample_feedback_data["description"]
    )

    retrieved_feedback = feedback_collector.get_feedback(feedback.id)
    assert retrieved_feedback is not None
    assert retrieved_feedback.id == feedback.id

    # 존재하지 않는 ID로 조회
    assert feedback_collector.get_feedback("non-existent-id") is None

def test_get_feedbacks_by_plan(populated_collector, multiple_feedbacks):
    """계획별 피드백 조회 테스트"""
    plan_id = multiple_feedbacks[0]["plan_id"]
    feedbacks = populated_collector.get_feedbacks_by_plan(plan_id)

    assert len(feedbacks) == len(multiple_feedbacks)
    for feedback in feedbacks:
        assert feedback.plan_id == plan_id

def test_get_feedbacks_by_type(populated_collector):
    """유형별 피드백 조회 테스트"""
    # 실행 관련 피드백 조회
    execution_feedbacks = populated_collector.get_feedbacks_by_type(FeedbackType.EXECUTION)
    assert len(execution_feedbacks) == 1
    assert all(f.type == FeedbackType.EXECUTION for f in execution_feedbacks)

    # 성능 관련 피드백 조회
    performance_feedbacks = populated_collector.get_feedbacks_by_type(FeedbackType.PERFORMANCE)
    assert len(performance_feedbacks) == 1
    assert all(f.type == FeedbackType.PERFORMANCE for f in performance_feedbacks)

def test_get_feedbacks_by_severity(populated_collector):
    """중요도별 피드백 조회 테스트"""
    # 중간 중요도 피드백 조회
    medium_feedbacks = populated_collector.get_feedbacks_by_severity(FeedbackSeverity.MEDIUM)
    assert len(medium_feedbacks) == 2
    assert all(f.severity == FeedbackSeverity.MEDIUM for f in medium_feedbacks)

    # 높은 중요도 피드백 조회
    high_feedbacks = populated_collector.get_feedbacks_by_severity(FeedbackSeverity.HIGH)
    assert len(high_feedbacks) == 1
    assert all(f.severity == FeedbackSeverity.HIGH for f in high_feedbacks)

def test_update_feedback_status(feedback_collector, sample_feedback_data):
    """피드백 상태 업데이트 테스트"""
    feedback = feedback_collector.create_feedback(
        plan_id=sample_feedback_data["plan_id"],
        type=sample_feedback_data["type"],
        severity=sample_feedback_data["severity"],
        title=sample_feedback_data["title"],
        description=sample_feedback_data["description"]
    )

    # 상태 업데이트
    updated_feedback = feedback_collector.update_feedback_status(
        feedback.id,
        FeedbackStatus.IN_REVIEW
    )
    assert updated_feedback is not None
    assert updated_feedback.status == FeedbackStatus.IN_REVIEW

    # 존재하지 않는 ID로 업데이트 시도
    assert feedback_collector.update_feedback_status(
        "non-existent-id",
        FeedbackStatus.IN_REVIEW
    ) is None

def test_add_feedback_metric(feedback_collector, sample_feedback_data):
    """피드백 메트릭 추가 테스트"""
    feedback = feedback_collector.create_feedback(
        plan_id=sample_feedback_data["plan_id"],
        type=sample_feedback_data["type"],
        severity=sample_feedback_data["severity"],
        title=sample_feedback_data["title"],
        description=sample_feedback_data["description"]
    )

    # 메트릭 추가
    updated_feedback = feedback_collector.add_feedback_metric(
        feedback.id,
        "cpu_usage",
        75.5
    )
    assert updated_feedback is not None
    assert updated_feedback.metrics["cpu_usage"] == 75.5

    # 존재하지 않는 ID로 메트릭 추가 시도
    assert feedback_collector.add_feedback_metric(
        "non-existent-id",
        "memory",
        1024
    ) is None

def test_add_feedback_tag(feedback_collector, sample_feedback_data):
    """피드백 태그 추가 테스트"""
    feedback = feedback_collector.create_feedback(
        plan_id=sample_feedback_data["plan_id"],
        type=sample_feedback_data["type"],
        severity=sample_feedback_data["severity"],
        title=sample_feedback_data["title"],
        description=sample_feedback_data["description"]
    )

    # 태그 추가
    updated_feedback = feedback_collector.add_feedback_tag(
        feedback.id,
        "new_tag"
    )
    assert updated_feedback is not None
    assert "new_tag" in updated_feedback.tags

    # 존재하지 않는 ID로 태그 추가 시도
    assert feedback_collector.add_feedback_tag(
        "non-existent-id",
        "test_tag"
    ) is None

def test_delete_feedback(feedback_collector, sample_feedback_data):
    """피드백 삭제 테스트"""
    feedback = feedback_collector.create_feedback(
        plan_id=sample_feedback_data["plan_id"],
        type=sample_feedback_data["type"],
        severity=sample_feedback_data["severity"],
        title=sample_feedback_data["title"],
        description=sample_feedback_data["description"]
    )

    # 피드백 삭제
    assert feedback_collector.delete_feedback(feedback.id) is True
    assert feedback_collector.get_feedback(feedback.id) is None

    # 존재하지 않는 ID로 삭제 시도
    assert feedback_collector.delete_feedback("non-existent-id") is False

def test_get_all_feedbacks(populated_collector, multiple_feedbacks):
    """모든 피드백 조회 테스트"""
    all_feedbacks = populated_collector.get_all_feedbacks()
    assert len(all_feedbacks) == len(multiple_feedbacks)

def test_get_feedback_count(populated_collector, multiple_feedbacks):
    """피드백 수 조회 테스트"""
    assert populated_collector.get_feedback_count() == len(multiple_feedbacks)

def test_clear_feedbacks(populated_collector):
    """모든 피드백 삭제 테스트"""
    assert populated_collector.get_feedback_count() > 0
    populated_collector.clear_feedbacks()
    assert populated_collector.get_feedback_count() == 0
