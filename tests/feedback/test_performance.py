"""
피드백 시스템의 성능 테스트를 정의하는 모듈입니다.
"""

import pytest
import time
import psutil
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
from memory_profiler import profile

from app.feedback.models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    ImprovementType,
    ImprovementSuggestion
)
from app.feedback.pattern_matcher import PatternMatcher
from app.feedback.priority_manager import PriorityManager
from app.feedback.result_tracker import ResultTracker
from app.feedback.suggester import ImprovementSuggester

# 성능 테스트를 위한 데이터 생성 유틸리티
def generate_test_feedbacks(count: int) -> List[Feedback]:
    """테스트용 피드백 데이터를 생성합니다."""
    now = datetime.now()
    feedbacks = []

    for i in range(count):
        feedback = Feedback(
            id=f"fb-{i}",
            plan_id=f"plan-{i % 10}",
            type=FeedbackType.PERFORMANCE if i % 3 == 0 else \
                 FeedbackType.ERROR if i % 3 == 1 else \
                 FeedbackType.RESOURCE,
            severity=FeedbackSeverity.HIGH if i % 4 == 0 else \
                    FeedbackSeverity.MEDIUM if i % 4 == 1 else \
                    FeedbackSeverity.LOW,
            title=f"Feedback {i}",
            description=f"Test feedback {i}",
            created_at=now - timedelta(minutes=i)
        )

        # 메트릭 추가
        feedback.add_metric("response_time", 100 + (i % 500))
        feedback.add_metric("cpu_usage", 50 + (i % 50))
        feedback.add_metric("memory_usage", 60 + (i % 40))

        feedbacks.append(feedback)

    return feedbacks

@pytest.fixture
def large_feedback_set():
    """대량의 테스트 피드백을 생성합니다."""
    return generate_test_feedbacks(1000)

@pytest.fixture
def very_large_feedback_set():
    """매우 큰 규모의 테스트 피드백을 생성합니다."""
    return generate_test_feedbacks(10000)

def measure_execution_time(func):
    """함수 실행 시간을 측정하는 데코레이터."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} 실행 시간: {execution_time:.2f}초")
        return result, execution_time
    return wrapper

def measure_memory_usage(func):
    """함수의 메모리 사용량을 측정하는 데코레이터."""
    def wrapper(*args, **kwargs):
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        result = func(*args, **kwargs)
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        print(f"{func.__name__} 메모리 사용량: {memory_used:.2f}MB")
        return result, memory_used
    return wrapper

@pytest.mark.slow
@pytest.mark.performance
class TestPatternMatcherPerformance:
    """PatternMatcher 성능 테스트."""

    @measure_execution_time
    def test_pattern_matching_large_dataset(self, large_feedback_set):
        """대량의 피드백에 대한 패턴 매칭 성능을 테스트합니다."""
        matcher = PatternMatcher()
        patterns = matcher.find_patterns(large_feedback_set)
        assert len(patterns) > 0
        return patterns

    @measure_memory_usage
    def test_pattern_matching_memory_usage(self, large_feedback_set):
        """패턴 매칭의 메모리 사용량을 테스트합니다."""
        matcher = PatternMatcher()
        patterns = matcher.find_patterns(large_feedback_set)
        assert len(patterns) > 0
        return patterns

    def test_pattern_matching_scalability(self, large_feedback_set, very_large_feedback_set):
        """패턴 매칭의 확장성을 테스트합니다."""
        matcher = PatternMatcher()

        # 중간 규모 데이터셋 처리 시간 측정
        start_time = time.time()
        patterns1 = matcher.find_patterns(large_feedback_set)
        time1 = time.time() - start_time

        # 대규모 데이터셋 처리 시간 측정
        start_time = time.time()
        patterns2 = matcher.find_patterns(very_large_feedback_set)
        time2 = time.time() - start_time

        # 처리 시간 비율 확인 (선형적 증가 여부)
        time_ratio = time2 / time1
        size_ratio = len(very_large_feedback_set) / len(large_feedback_set)

        print(f"시간 비율: {time_ratio:.2f}, 크기 비율: {size_ratio:.2f}")
        assert time_ratio <= size_ratio * 1.5  # 1.5배 이내의 증가율 허용

@pytest.mark.slow
@pytest.mark.performance
class TestPriorityManagerPerformance:
    """PriorityManager 성능 테스트."""

    @measure_execution_time
    def test_priority_calculation_large_dataset(self, large_feedback_set):
        """대량의 개선사항에 대한 우선순위 계산 성능을 테스트합니다."""
        manager = PriorityManager()
        suggestions = [
            ImprovementSuggestion(
                id=f"imp-{i}",
                type=ImprovementType.PERFORMANCE,
                title=f"Improvement {i}",
                description=f"Test improvement {i}",
                priority=0.5
            )
            for i in range(100)
        ]

        feedbacks_map = {s.id: large_feedback_set for s in suggestions}
        sorted_suggestions = manager.sort_suggestions(suggestions, feedbacks_map)
        assert len(sorted_suggestions) == len(suggestions)
        return sorted_suggestions

@pytest.mark.slow
@pytest.mark.performance
class TestResultTrackerPerformance:
    """ResultTracker 성능 테스트."""

    @measure_execution_time
    def test_result_tracking_large_dataset(self, large_feedback_set):
        """대량의 피드백에 대한 결과 추적 성능을 테스트합니다."""
        tracker = ResultTracker()
        suggestion = ImprovementSuggestion(
            id="imp-test",
            type=ImprovementType.PERFORMANCE,
            title="Test Improvement",
            description="Test improvement",
            priority=0.7
        )

        result = tracker.track_feedback_changes(suggestion, large_feedback_set)
        assert "total_feedbacks" in result
        return result

@pytest.mark.slow
@pytest.mark.performance
class TestSuggesterPerformance:
    """ImprovementSuggester 성능 테스트."""

    @measure_execution_time
    def test_suggestion_generation_large_dataset(self, large_feedback_set):
        """대량의 피드백에 대한 개선사항 제안 성능을 테스트합니다."""
        suggester = ImprovementSuggester()
        suggestions = suggester.analyze_feedbacks(large_feedback_set)
        assert len(suggestions) > 0
        return suggestions

    @measure_memory_usage
    def test_suggestion_memory_usage(self, large_feedback_set):
        """개선사항 제안의 메모리 사용량을 테스트합니다."""
        suggester = ImprovementSuggester()
        suggestions = suggester.analyze_feedbacks(large_feedback_set)
        assert len(suggestions) > 0
        return suggestions

    def test_suggestion_response_time(self, large_feedback_set):
        """개선사항 제안의 응답 시간을 테스트합니다."""
        suggester = ImprovementSuggester()
        response_times = []

        # 여러 번 실행하여 평균 응답 시간 측정
        for _ in range(5):
            start_time = time.time()
            suggestions = suggester.analyze_feedbacks(large_feedback_set)
            response_time = time.time() - start_time
            response_times.append(response_time)

        avg_response_time = np.mean(response_times)
        std_response_time = np.std(response_times)

        print(f"평균 응답 시간: {avg_response_time:.2f}초")
        print(f"표준 편차: {std_response_time:.2f}초")

        # 응답 시간이 일정 시간 이내인지 확인
        assert avg_response_time < 5.0  # 5초 이내
        # 응답 시간의 편차가 크지 않은지 확인
        assert std_response_time < 1.0  # 1초 이내의 편차
