"""
피드백 시스템 테스트를 위한 공통 fixture를 정의하는 모듈입니다.
"""

import os
import pytest
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.feedback.models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    ImprovementType,
    ImprovementStatus,
    ImprovementSuggestion
)
from app.feedback.collector import FeedbackCollector
from app.feedback.analyzer import FeedbackAnalyzer
from app.feedback.storage import FeedbackStorage

@pytest.fixture
def sample_feedback_data() -> Dict:
    """샘플 피드백 데이터를 제공하는 픽스처"""
    return {
        "id": "test-feedback-001",
        "plan_id": "test-plan-001",
        "type": FeedbackType.EXECUTION,
        "severity": FeedbackSeverity.MEDIUM,
        "title": "테스트 피드백",
        "description": "테스트를 위한 샘플 피드백입니다.",
        "step_index": 1,
        "metrics": {"duration": 10.5, "memory": 256},
        "tags": ["test", "sample"]
    }

@pytest.fixture
def sample_feedback(sample_feedback_data) -> Feedback:
    """샘플 Feedback 객체를 제공하는 픽스처"""
    return Feedback(**sample_feedback_data)

@pytest.fixture
def feedback_collector() -> FeedbackCollector:
    """FeedbackCollector 인스턴스를 제공하는 픽스처"""
    return FeedbackCollector()

@pytest.fixture
def feedback_analyzer() -> FeedbackAnalyzer:
    """FeedbackAnalyzer 인스턴스를 제공하는 픽스처"""
    return FeedbackAnalyzer()

@pytest.fixture
def temp_storage_dir():
    """임시 저장소 디렉토리를 제공하는 픽스처"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def feedback_storage(temp_storage_dir) -> FeedbackStorage:
    """FeedbackStorage 인스턴스를 제공하는 픽스처"""
    return FeedbackStorage(storage_dir=temp_storage_dir)

@pytest.fixture
def multiple_feedbacks() -> List[Dict]:
    """여러 개의 샘플 피드백 데이터를 제공하는 픽스처"""
    return [
        {
            "id": f"test-feedback-{i:03d}",
            "plan_id": "test-plan-001",
            "type": feedback_type,
            "severity": severity,
            "title": f"테스트 피드백 {i}",
            "description": f"테스트를 위한 샘플 피드백 {i}입니다.",
            "step_index": i,
            "metrics": {"duration": float(i * 10), "memory": i * 100},
            "tags": ["test", f"sample-{i}"]
        }
        for i, (feedback_type, severity) in enumerate([
            (FeedbackType.EXECUTION, FeedbackSeverity.LOW),
            (FeedbackType.PERFORMANCE, FeedbackSeverity.MEDIUM),
            (FeedbackType.ERROR, FeedbackSeverity.HIGH),
            (FeedbackType.USABILITY, FeedbackSeverity.CRITICAL),
            (FeedbackType.SUGGESTION, FeedbackSeverity.MEDIUM)
        ])
    ]

@pytest.fixture
def populated_collector(feedback_collector, multiple_feedbacks) -> FeedbackCollector:
    """여러 피드백이 등록된 FeedbackCollector를 제공하는 픽스처"""
    for feedback_data in multiple_feedbacks:
        feedback_collector.create_feedback(
            plan_id=feedback_data["plan_id"],
            type=feedback_data["type"],
            severity=feedback_data["severity"],
            title=feedback_data["title"],
            description=feedback_data["description"],
            step_index=feedback_data["step_index"],
            metrics=feedback_data["metrics"],
            tags=feedback_data["tags"]
        )
    return feedback_collector

@pytest.fixture
def populated_storage(feedback_storage, multiple_feedbacks) -> FeedbackStorage:
    """여러 피드백이 저장된 FeedbackStorage를 제공하는 픽스처"""
    for feedback_data in multiple_feedbacks:
        feedback = Feedback(**feedback_data)
        feedback_storage.save_feedback(feedback)
    return feedback_storage

@pytest.fixture
def base_feedback():
    """기본 피드백 객체를 생성합니다."""
    return Feedback(
        id="fb-test",
        plan_id="plan-1",
        type=FeedbackType.PERFORMANCE,
        severity=FeedbackSeverity.MEDIUM,
        title="Test Feedback",
        description="Test feedback description"
    )

@pytest.fixture
def base_suggestion():
    """기본 개선사항 객체를 생성합니다."""
    return ImprovementSuggestion(
        id="imp-test",
        type=ImprovementType.PERFORMANCE,
        title="Test Improvement",
        description="Test improvement description",
        priority=0.5
    )

@pytest.fixture
def time_window():
    """테스트용 시간 윈도우를 생성합니다."""
    return timedelta(days=7)

@pytest.fixture
def base_metrics():
    """기본 메트릭 데이터를 생성합니다."""
    return {
        "response_time": 500,  # ms
        "cpu_usage": 80,       # %
        "memory_usage": 70,    # %
        "error_rate": 5        # %
    }

@pytest.fixture
def feedback_factory():
    """피드백 객체를 생성하는 팩토리 함수를 반환합니다."""
    def create_feedback(
        id_prefix: str,
        feedback_type: FeedbackType,
        severity: FeedbackSeverity,
        created_at: datetime,
        metrics: Dict = None
    ) -> Feedback:
        feedback = Feedback(
            id=f"{id_prefix}-{created_at.timestamp()}",
            plan_id="plan-1",
            type=feedback_type,
            severity=severity,
            title=f"Feedback {feedback_type.value}",
            description=f"Test feedback of type {feedback_type.value}",
            created_at=created_at
        )

        if metrics:
            for key, value in metrics.items():
                feedback.add_metric(key, value)

        return feedback

    return create_feedback

@pytest.fixture
def suggestion_factory():
    """개선사항 객체를 생성하는 팩토리 함수를 반환합니다."""
    def create_suggestion(
        id_prefix: str,
        improvement_type: ImprovementType,
        priority: float,
        status: ImprovementStatus = ImprovementStatus.PROPOSED,
        metrics: Dict = None,
        expected_benefits: Dict = None,
        implementation_cost: Dict = None
    ) -> ImprovementSuggestion:
        suggestion = ImprovementSuggestion(
            id=f"{id_prefix}-{datetime.now().timestamp()}",
            type=improvement_type,
            title=f"Improvement {improvement_type.value}",
            description=f"Test improvement of type {improvement_type.value}",
            priority=priority
        )

        suggestion.status = status

        if metrics:
            suggestion.metrics = metrics
        if expected_benefits:
            suggestion.expected_benefits = expected_benefits
        if implementation_cost:
            suggestion.implementation_cost = implementation_cost

        return suggestion

    return create_suggestion
