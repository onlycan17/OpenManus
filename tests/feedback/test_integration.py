"""
피드백 시스템의 통합 테스트를 정의하는 모듈입니다.
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict

from app.feedback.models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    ImprovementType,
    ImprovementStatus,
    ImprovementSuggestion
)
from app.feedback.pattern_matcher import PatternMatcher
from app.feedback.priority_manager import PriorityManager
from app.feedback.result_tracker import ResultTracker
from app.feedback.suggester import ImprovementSuggester

@pytest.fixture
def feedback_system():
    """전체 피드백 시스템 컴포넌트를 생성합니다."""
    return {
        "pattern_matcher": PatternMatcher(),
        "priority_manager": PriorityManager(),
        "result_tracker": ResultTracker(),
        "suggester": ImprovementSuggester()
    }

@pytest.fixture
def sample_feedbacks():
    """테스트용 피드백 데이터를 생성합니다."""
    now = datetime.now()
    feedbacks = []

    # 성능 관련 피드백
    for i in range(3):
        feedback = Feedback(
            id=f"fb-perf-{i}",
            plan_id="plan-1",
            type=FeedbackType.PERFORMANCE,
            severity=FeedbackSeverity.HIGH,
            title=f"Performance Issue {i}",
            description="High response time detected",
            created_at=now - timedelta(hours=i)
        )
        feedback.add_metric("response_time", 500 + i * 100)
        feedback.add_metric("cpu_usage", 80 + i * 5)
        feedbacks.append(feedback)

    # 에러 관련 피드백
    for i in range(2):
        feedback = Feedback(
            id=f"fb-err-{i}",
            plan_id="plan-1",
            type=FeedbackType.ERROR,
            severity=FeedbackSeverity.CRITICAL,
            title=f"Error {i}",
            description="System error occurred",
            created_at=now - timedelta(hours=i*2)
        )
        feedback.add_metric("error_count", 5 + i)
        feedbacks.append(feedback)

    return feedbacks

@pytest.mark.integration
class TestFeedbackSystemIntegration:
    """피드백 시스템 통합 테스트."""

    def test_complete_workflow(self, feedback_system, sample_feedbacks):
        """전체 워크플로우를 테스트합니다."""
        # 1. 패턴 분석
        patterns = feedback_system["pattern_matcher"].find_patterns(sample_feedbacks)
        assert len(patterns) > 0

        # 2. 개선사항 제안
        suggestions = feedback_system["suggester"].analyze_feedbacks(sample_feedbacks)
        assert len(suggestions) > 0
        suggestion = suggestions[0]

        # 3. 우선순위 계산
        feedbacks_map = {suggestion.id: sample_feedbacks}
        sorted_suggestions = feedback_system["priority_manager"].sort_suggestions(
            suggestions,
            feedbacks_map
        )
        assert len(sorted_suggestions) == len(suggestions)

        # 4. 결과 추적
        metrics_before = {
            "response_time": 500,
            "cpu_usage": 80,
            "error_count": 5
        }
        metrics_after = {
            "response_time": 300,
            "cpu_usage": 60,
            "error_count": 2
        }

        result = feedback_system["result_tracker"].track_implementation(
            suggestion,
            metrics_before,
            metrics_after
        )
        assert result["success"]

        # 5. 상태 업데이트 및 이력 조회
        feedback_system["suggester"].update_suggestion_status(
            suggestion.id,
            ImprovementStatus.IMPLEMENTED
        )
        metrics_history, feedback_history = feedback_system["suggester"].get_implementation_history(
            suggestion.id
        )
        assert len(metrics_history) > 0

    def test_error_handling(self, feedback_system):
        """에러 처리를 테스트합니다."""
        # 1. 잘못된 ID로 개선사항 조회
        suggestion = feedback_system["suggester"].get_suggestion("non-existent")
        assert suggestion is None

        # 2. 빈 피드백 목록으로 패턴 분석
        patterns = feedback_system["pattern_matcher"].find_patterns([])
        assert len(patterns) == 0

        # 3. 잘못된 상태로 업데이트
        success = feedback_system["suggester"].update_suggestion_status(
            "non-existent",
            ImprovementStatus.IMPLEMENTED
        )
        assert not success

    def test_data_consistency(self, feedback_system, sample_feedbacks):
        """데이터 일관성을 테스트합니다."""
        # 1. 개선사항 제안 및 조회
        suggestions = feedback_system["suggester"].analyze_feedbacks(sample_feedbacks)
        suggestion = suggestions[0]
        retrieved = feedback_system["suggester"].get_suggestion(suggestion.id)

        assert retrieved is not None
        assert retrieved.id == suggestion.id
        assert retrieved.type == suggestion.type
        assert retrieved.priority == suggestion.priority

        # 2. 상태 업데이트 후 일관성 확인
        feedback_system["suggester"].update_suggestion_status(
            suggestion.id,
            ImprovementStatus.IMPLEMENTING
        )
        updated = feedback_system["suggester"].get_suggestion(suggestion.id)
        assert updated.status == ImprovementStatus.IMPLEMENTING

        # 3. 결과 추적 데이터 일관성
        metrics_before = {"response_time": 500}
        metrics_after = {"response_time": 300}

        result = feedback_system["result_tracker"].track_implementation(
            suggestion,
            metrics_before,
            metrics_after
        )

        metrics_history, _ = feedback_system["suggester"].get_implementation_history(
            suggestion.id
        )
        assert len(metrics_history) > 0
        assert "response_time" in metrics_history[0]["metrics"]

    def test_component_interaction(self, feedback_system, sample_feedbacks):
        """컴포넌트 간 상호작용을 테스트합니다."""
        # 1. 패턴 매칭 -> 개선사항 제안
        patterns = feedback_system["pattern_matcher"].find_patterns(sample_feedbacks)
        suggestions = feedback_system["suggester"].analyze_feedbacks(sample_feedbacks)

        # 패턴과 제안사항의 관계 확인
        assert len(suggestions) > 0
        suggestion = suggestions[0]
        assert any(
            p["type"] == "performance"
            for p in patterns
            if suggestion.type == ImprovementType.PERFORMANCE
        )

        # 2. 개선사항 제안 -> 우선순위 계산
        feedbacks_map = {s.id: sample_feedbacks for s in suggestions}
        sorted_suggestions = feedback_system["priority_manager"].sort_suggestions(
            suggestions,
            feedbacks_map
        )

        # 우선순위 정렬 확인
        assert len(sorted_suggestions) == len(suggestions)
        assert all(
            sorted_suggestions[i].priority >= sorted_suggestions[i+1].priority
            for i in range(len(sorted_suggestions)-1)
        )

        # 3. 우선순위 계산 -> 결과 추적
        high_priority = sorted_suggestions[0]
        metrics_before = {
            "response_time": 500,
            "cpu_usage": 80
        }
        metrics_after = {
            "response_time": 300,
            "cpu_usage": 60
        }

        result = feedback_system["result_tracker"].track_implementation(
            high_priority,
            metrics_before,
            metrics_after
        )

        # 결과 추적 확인
        assert result["success"]
        assert "improvements" in result
        assert all(
            result["improvements"][metric]["improvement_rate"] > 0
            for metric in metrics_before.keys()
        )

    def test_performance_requirements(self, feedback_system):
        """성능 요구사항 충족을 테스트합니다."""
        # 1. 대량의 피드백 생성
        now = datetime.now()
        large_feedbacks = []

        for i in range(1000):
            feedback = Feedback(
                id=f"fb-{i}",
                plan_id=f"plan-{i % 10}",
                type=FeedbackType.PERFORMANCE,
                severity=FeedbackSeverity.MEDIUM,
                title=f"Feedback {i}",
                description="Test feedback",
                created_at=now - timedelta(minutes=i)
            )
            feedback.add_metric("response_time", 100 + (i % 500))
            large_feedbacks.append(feedback)

        # 2. 처리 시간 측정
        start_time = time.time()

        # 패턴 분석
        patterns = feedback_system["pattern_matcher"].find_patterns(large_feedbacks)
        pattern_time = time.time() - start_time

        # 개선사항 제안
        start_time = time.time()
        suggestions = feedback_system["suggester"].analyze_feedbacks(large_feedbacks)
        suggestion_time = time.time() - start_time

        # 3. 성능 요구사항 검증
        assert pattern_time < 5.0  # 패턴 분석은 5초 이내
        assert suggestion_time < 10.0  # 개선사항 제안은 10초 이내
        assert len(patterns) > 0
        assert len(suggestions) > 0
