"""
피드백 분석기에 대한 테스트를 구현하는 모듈입니다.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List

from app.feedback.models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    FeedbackStatus
)
from app.feedback.analyzer import FeedbackAnalyzer, FeedbackAnalysis

def test_feedback_analyzer_initialization(feedback_analyzer):
    """FeedbackAnalyzer 초기화 테스트"""
    assert isinstance(feedback_analyzer, FeedbackAnalyzer)

def test_analyze_feedbacks_empty():
    """빈 피드백 목록 분석 테스트"""
    analyzer = FeedbackAnalyzer()
    analysis = analyzer.analyze_feedbacks([])

    assert isinstance(analysis, FeedbackAnalysis)
    assert analysis.total_count == 0
    assert len(analysis.type_distribution) == 0
    assert len(analysis.severity_distribution) == 0
    assert len(analysis.status_distribution) == 0
    assert len(analysis.common_tags) == 0
    assert len(analysis.metrics_summary) == 0
    assert len(analysis.time_based_stats) == 0

def test_analyze_feedbacks(populated_collector):
    """피드백 분석 테스트"""
    analyzer = FeedbackAnalyzer()
    feedbacks = populated_collector.get_all_feedbacks()
    analysis = analyzer.analyze_feedbacks(feedbacks)

    # 기본 통계 검증
    assert analysis.total_count == len(feedbacks)
    assert len(analysis.type_distribution) > 0
    assert len(analysis.severity_distribution) > 0
    assert len(analysis.status_distribution) > 0

    # 분포 검증
    assert analysis.type_distribution[FeedbackType.EXECUTION] == 1
    assert analysis.type_distribution[FeedbackType.PERFORMANCE] == 1
    assert analysis.severity_distribution[FeedbackSeverity.MEDIUM] == 2
    assert analysis.status_distribution[FeedbackStatus.NEW] == len(feedbacks)

    # 태그 분석 검증
    assert len(analysis.common_tags) > 0
    assert ("test", len(feedbacks)) in analysis.common_tags

    # 메트릭 분석 검증
    assert "duration" in analysis.metrics_summary
    assert "memory" in analysis.metrics_summary
    for metric in analysis.metrics_summary.values():
        assert "count" in metric
        assert "min" in metric
        assert "max" in metric
        assert "avg" in metric

def test_analyze_feedbacks_with_time_window(populated_collector):
    """시간 윈도우를 적용한 피드백 분석 테스트"""
    analyzer = FeedbackAnalyzer()
    feedbacks = populated_collector.get_all_feedbacks()

    # 현재 시점부터 1일 전까지의 피드백만 분석
    time_window = timedelta(days=1)
    analysis = analyzer.analyze_feedbacks(feedbacks, time_window)

    assert analysis.total_count == len(feedbacks)  # 모든 피드백이 최근 1일 내에 생성됨

    # 7일 전 피드백 분석
    old_time_window = timedelta(days=7)
    old_analysis = analyzer.analyze_feedbacks(feedbacks, old_time_window)

    assert old_analysis.total_count == len(feedbacks)  # 모든 피드백이 7일 내에 생성됨

def test_get_critical_feedbacks(populated_collector):
    """중요 피드백 추출 테스트"""
    analyzer = FeedbackAnalyzer()
    feedbacks = populated_collector.get_all_feedbacks()

    critical_feedbacks = analyzer.get_critical_feedbacks(feedbacks)
    assert len(critical_feedbacks) == 1
    assert all(f.severity == FeedbackSeverity.CRITICAL for f in critical_feedbacks)

def test_get_trending_issues(populated_collector):
    """트렌드 이슈 분석 테스트"""
    analyzer = FeedbackAnalyzer()
    feedbacks = populated_collector.get_all_feedbacks()

    # 최근 1일 동안의 트렌드 분석
    trends = analyzer.get_trending_issues(
        feedbacks,
        timedelta(days=1),
        min_occurrence=1
    )

    assert len(trends) > 0
    assert isinstance(trends[0], tuple)
    assert len(trends[0]) == 2
    assert isinstance(trends[0][0], str)  # 태그
    assert isinstance(trends[0][1], int)  # 발생 횟수

def test_get_performance_metrics(populated_collector):
    """성능 메트릭 분석 테스트"""
    analyzer = FeedbackAnalyzer()
    feedbacks = populated_collector.get_all_feedbacks()

    metrics = analyzer.get_performance_metrics(feedbacks)
    assert isinstance(metrics, dict)

    # 성능 관련 피드백의 메트릭 검증
    performance_feedbacks = [
        f for f in feedbacks
        if f.type == FeedbackType.PERFORMANCE
    ]

    if performance_feedbacks:
        assert len(metrics) > 0
        for metric_name, stats in metrics.items():
            assert "count" in stats
            assert "min" in stats
            assert "max" in stats
            assert "avg" in stats

def test_get_feedback_summary(populated_collector):
    """피드백 요약 정보 생성 테스트"""
    analyzer = FeedbackAnalyzer()
    feedbacks = populated_collector.get_all_feedbacks()

    summary = analyzer.get_feedback_summary(feedbacks)
    assert isinstance(summary, dict)
    assert "total_count" in summary
    assert "type_distribution" in summary
    assert "severity_distribution" in summary
    assert "status_distribution" in summary

    assert summary["total_count"] == len(feedbacks)
    assert len(summary["type_distribution"]) > 0
    assert len(summary["severity_distribution"]) > 0
    assert len(summary["status_distribution"]) > 0

def test_get_resolution_rate(populated_collector):
    """피드백 해결률 계산 테스트"""
    analyzer = FeedbackAnalyzer()
    feedbacks = populated_collector.get_all_feedbacks()

    # 초기 상태에서는 모든 피드백이 NEW 상태
    initial_rate = analyzer.get_resolution_rate(feedbacks)
    assert initial_rate == 0.0

    # 일부 피드백을 해결 상태로 변경
    for feedback in feedbacks[:2]:
        feedback.status = FeedbackStatus.IMPLEMENTED

    updated_rate = analyzer.get_resolution_rate(feedbacks)
    assert updated_rate == (2 / len(feedbacks)) * 100

def test_analyze_feedbacks_with_invalid_metrics():
    """잘못된 메트릭이 포함된 피드백 분석 테스트"""
    analyzer = FeedbackAnalyzer()

    # 잘못된 메트릭이 포함된 피드백 생성
    feedback = Feedback(
        id="test-001",
        plan_id="plan-001",
        type=FeedbackType.PERFORMANCE,
        severity=FeedbackSeverity.MEDIUM,
        title="Test Feedback",
        description="Test Description",
        metrics={
            "valid_metric": 100,
            "invalid_metric": "not_a_number"  # 숫자가 아닌 값
        }
    )

    analysis = analyzer.analyze_feedbacks([feedback])

    # 유효한 메트릭만 분석되어야 함
    assert "valid_metric" in analysis.metrics_summary
    assert "invalid_metric" not in analysis.metrics_summary
