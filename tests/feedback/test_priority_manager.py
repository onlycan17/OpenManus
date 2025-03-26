"""
PriorityManager 클래스의 테스트를 정의하는 모듈입니다.
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from app.feedback.models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    ImprovementType,
    ImprovementSuggestion
)
from app.feedback.priority_manager import PriorityManager

@pytest.fixture
def priority_manager():
    """PriorityManager 인스턴스를 생성합니다."""
    return PriorityManager()

@pytest.fixture
def sample_suggestion():
    """테스트용 개선사항을 생성합니다."""
    return ImprovementSuggestion(
        id="imp-test",
        type=ImprovementType.PERFORMANCE,
        title="Performance Improvement",
        description="Improve system performance",
        priority=0.5,
        expected_benefits={
            "performance_improvement": 0.4,
            "resource_saving": 0.3,
            "reliability_improvement": 0.2
        },
        implementation_cost={
            "development_time": 0.5,
            "resource_requirement": 0.3,
            "risk_level": 0.2
        }
    )

@pytest.fixture
def sample_feedbacks():
    """테스트용 피드백 목록을 생성합니다."""
    now = datetime.now()
    feedbacks = []

    # 심각도가 높은 최근 피드백
    for i in range(3):
        feedbacks.append(Feedback(
            id=f"fb-high-{i}",
            plan_id="plan-1",
            type=FeedbackType.PERFORMANCE,
            severity=FeedbackSeverity.HIGH,
            title=f"High Priority Issue {i}",
            description="Critical performance issue",
            created_at=now - timedelta(hours=i)
        ))

    # 심각도가 중간인 이전 피드백
    for i in range(2):
        feedbacks.append(Feedback(
            id=f"fb-medium-{i}",
            plan_id="plan-1",
            type=FeedbackType.PERFORMANCE,
            severity=FeedbackSeverity.MEDIUM,
            title=f"Medium Priority Issue {i}",
            description="Performance issue",
            created_at=now - timedelta(days=i+1)
        ))

    return feedbacks

def test_priority_manager_initialization(priority_manager):
    """PriorityManager 초기화를 테스트합니다."""
    assert isinstance(priority_manager, PriorityManager)
    assert sum(priority_manager.weights.values()) == 1.0  # 가중치 합이 1
    assert all(0 <= w <= 1 for w in priority_manager.weights.values())  # 가중치 범위 검증

def test_calculate_severity_score(priority_manager, sample_feedbacks):
    """심각도 점수 계산을 테스트합니다."""
    score = priority_manager._calculate_severity_score(sample_feedbacks)
    assert 0 <= score <= 1
    assert score > 0.7  # 높은 심각도의 피드백이 많으므로 높은 점수

def test_calculate_frequency_score(priority_manager, sample_feedbacks):
    """발생 빈도 점수 계산을 테스트합니다."""
    score = priority_manager._calculate_frequency_score(sample_feedbacks)
    assert 0 <= score <= 1
    assert score > 0  # 최근 피드백이 있으므로 0보다 큰 점수

def test_calculate_impact_score(priority_manager, sample_suggestion):
    """영향도 점수 계산을 테스트합니다."""
    score = priority_manager._calculate_impact_score(sample_suggestion)
    assert 0 <= score <= 1

    # 예상 이점이 없는 경우
    suggestion_no_benefits = ImprovementSuggestion(
        id="imp-test-2",
        type=ImprovementType.PERFORMANCE,
        title="Test",
        description="Test",
        priority=0.5
    )
    score_no_benefits = priority_manager._calculate_impact_score(suggestion_no_benefits)
    assert score_no_benefits == 0.5  # 기본값

def test_calculate_cost_score(priority_manager, sample_suggestion):
    """구현 비용 점수 계산을 테스트합니다."""
    score = priority_manager._calculate_cost_score(sample_suggestion)
    assert 0 <= score <= 1

    # 비용 정보가 없는 경우
    suggestion_no_cost = ImprovementSuggestion(
        id="imp-test-2",
        type=ImprovementType.PERFORMANCE,
        title="Test",
        description="Test",
        priority=0.5
    )
    score_no_cost = priority_manager._calculate_cost_score(suggestion_no_cost)
    assert score_no_cost == 0.5  # 기본값

def test_calculate_urgency_score(priority_manager, sample_feedbacks):
    """긴급도 점수 계산을 테스트합니다."""
    score = priority_manager._calculate_urgency_score(sample_feedbacks)
    assert 0 <= score <= 1
    assert score > 0.5  # 최근의 높은 심각도 피드백으로 인한 높은 점수

def test_calculate_priority(priority_manager, sample_suggestion, sample_feedbacks):
    """전체 우선순위 계산을 테스트합니다."""
    priority = priority_manager.calculate_priority(sample_suggestion, sample_feedbacks)
    assert 0 <= priority <= 1

    # 기본 점수와 가중 평균이 반영되었는지 확인
    base_score = priority_manager.type_base_scores[sample_suggestion.type]
    assert priority != base_score  # 가중 평균이 반영되어 다른 값

def test_sort_suggestions(priority_manager, sample_suggestion, sample_feedbacks):
    """개선사항 정렬을 테스트합니다."""
    # 여러 개선사항 생성
    suggestions = [
        sample_suggestion,
        ImprovementSuggestion(
            id="imp-test-2",
            type=ImprovementType.RELIABILITY,
            title="Reliability Improvement",
            description="Improve system reliability",
            priority=0.7
        ),
        ImprovementSuggestion(
            id="imp-test-3",
            type=ImprovementType.RESOURCE,
            title="Resource Optimization",
            description="Optimize resource usage",
            priority=0.3
        )
    ]

    # 피드백 매핑
    feedbacks_map = {
        "imp-test": sample_feedbacks,
        "imp-test-2": sample_feedbacks[:2],
        "imp-test-3": sample_feedbacks[2:]
    }

    sorted_suggestions = priority_manager.sort_suggestions(suggestions, feedbacks_map)
    assert len(sorted_suggestions) == len(suggestions)

    # 우선순위 순서로 정렬되었는지 확인
    priorities = [
        priority_manager.calculate_priority(s, feedbacks_map[s.id])
        for s in sorted_suggestions
    ]
    assert all(priorities[i] >= priorities[i+1] for i in range(len(priorities)-1))

def test_type_base_scores(priority_manager):
    """유형별 기본 우선순위 점수를 테스트합니다."""
    assert all(0 <= score <= 1 for score in priority_manager.type_base_scores.values())
    assert priority_manager.type_base_scores[ImprovementType.RELIABILITY] > \
           priority_manager.type_base_scores[ImprovementType.EFFICIENCY]  # 신뢰성이 효율성보다 높은 우선순위
