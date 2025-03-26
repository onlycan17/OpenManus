"""
개선사항을 제안하고 관리하는 모듈입니다.
"""

import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .models import (
    Feedback,
    ImprovementSuggestion,
    ImprovementType,
    ImprovementStatus
)
from .pattern_matcher import PatternMatcher
from .priority_manager import PriorityManager
from .result_tracker import ResultTracker

class ImprovementSuggester:
    """
    개선사항을 제안하고 관리하는 클래스입니다.
    """

    def __init__(self):
        """ImprovementSuggester 객체를 초기화합니다."""
        self.pattern_matcher = PatternMatcher()
        self.priority_manager = PriorityManager()
        self.result_tracker = ResultTracker()
        self.suggestions: Dict[str, ImprovementSuggestion] = {}
        self.feedback_map: Dict[str, List[str]] = {}  # suggestion_id -> feedback_ids

    def analyze_feedbacks(self, feedbacks: List[Feedback]) -> List[ImprovementSuggestion]:
        """
        피드백을 분석하여 개선사항을 제안합니다.

        Args:
            feedbacks: 분석할 피드백 목록

        Returns:
            List[ImprovementSuggestion]: 제안된 개선사항 목록
        """
        # 패턴 분석
        patterns = self.pattern_matcher.find_patterns(feedbacks)

        # 개선사항 생성
        new_suggestions = []
        for pattern in patterns:
            # 개선사항 유형 및 신뢰도 결정
            improvement_type, confidence = self.pattern_matcher.suggest_improvement_type(pattern)

            # 패턴의 중요도 계산
            significance = self.pattern_matcher.calculate_pattern_significance(pattern)

            # 개선사항 생성
            suggestion = self._create_suggestion(
                improvement_type=improvement_type,
                pattern=pattern,
                confidence=confidence,
                significance=significance,
                related_feedbacks=[f.id for f in feedbacks]
            )

            self.suggestions[suggestion.id] = suggestion
            self.feedback_map[suggestion.id] = [f.id for f in feedbacks]
            new_suggestions.append(suggestion)

        # 우선순위 기반 정렬
        feedback_dict = {
            suggestion.id: [f for f in feedbacks if f.id in self.feedback_map[suggestion.id]]
            for suggestion in new_suggestions
        }
        sorted_suggestions = self.priority_manager.sort_suggestions(new_suggestions, feedback_dict)

        return sorted_suggestions

    def get_suggestion(self, suggestion_id: str) -> Optional[ImprovementSuggestion]:
        """
        개선사항을 조회합니다.

        Args:
            suggestion_id: 개선사항 ID

        Returns:
            Optional[ImprovementSuggestion]: 조회된 개선사항
        """
        return self.suggestions.get(suggestion_id)

    def get_all_suggestions(
        self,
        status: Optional[ImprovementStatus] = None
    ) -> List[ImprovementSuggestion]:
        """
        모든 개선사항을 조회합니다.

        Args:
            status: 조회할 상태 (None이면 모든 상태)

        Returns:
            List[ImprovementSuggestion]: 개선사항 목록
        """
        if status:
            return [s for s in self.suggestions.values() if s.status == status]
        return list(self.suggestions.values())

    def update_suggestion_status(
        self,
        suggestion_id: str,
        new_status: ImprovementStatus
    ) -> bool:
        """
        개선사항의 상태를 업데이트합니다.

        Args:
            suggestion_id: 개선사항 ID
            new_status: 새로운 상태

        Returns:
            bool: 업데이트 성공 여부
        """
        suggestion = self.suggestions.get(suggestion_id)
        if suggestion:
            suggestion.update_status(new_status)
            return True
        return False

    def track_implementation_result(
        self,
        suggestion_id: str,
        before_metrics: Dict,
        after_metrics: Dict,
        new_feedbacks: List[Feedback]
    ) -> Dict:
        """
        개선사항 구현 결과를 추적합니다.

        Args:
            suggestion_id: 개선사항 ID
            before_metrics: 구현 전 메트릭
            after_metrics: 구현 후 메트릭
            new_feedbacks: 구현 후 수집된 새로운 피드백

        Returns:
            Dict: 추적 결과
        """
        suggestion = self.suggestions.get(suggestion_id)
        if not suggestion:
            raise ValueError(f"개선사항을 찾을 수 없습니다: {suggestion_id}")

        # 구현 결과 추적
        implementation_result = self.result_tracker.track_implementation(
            suggestion, before_metrics, after_metrics
        )

        # 피드백 변화 추적
        feedback_changes = self.result_tracker.track_feedback_changes(
            suggestion, new_feedbacks
        )

        # 성공 여부 평가
        is_successful, confidence, description = self.result_tracker.evaluate_success(
            suggestion, implementation_result, feedback_changes
        )

        # 결과 종합
        return {
            "suggestion_id": suggestion_id,
            "implementation_result": implementation_result,
            "feedback_changes": feedback_changes,
            "evaluation": {
                "success": is_successful,
                "confidence": confidence,
                "description": description
            }
        }

    def get_implementation_history(
        self,
        suggestion_id: str
    ) -> Tuple[List[Dict], List[Feedback]]:
        """
        개선사항의 구현 이력을 조회합니다.

        Args:
            suggestion_id: 개선사항 ID

        Returns:
            Tuple[List[Dict], List[Feedback]]: (메트릭 이력, 피드백 이력)
        """
        metrics_history = self.result_tracker.get_metrics_history(suggestion_id)
        feedback_history = self.result_tracker.get_feedback_history(suggestion_id)
        return metrics_history, feedback_history

    def _create_suggestion(
        self,
        improvement_type: ImprovementType,
        pattern: Dict,
        confidence: float,
        significance: float,
        related_feedbacks: List[str]
    ) -> ImprovementSuggestion:
        """개선사항을 생성합니다."""
        suggestion_id = f"imp-{uuid.uuid4().hex[:8]}"

        # 제목 생성
        if pattern["type"] == "metric_based":
            title = f"{pattern['metric_name']} 메트릭 개선 필요"
        elif pattern["type"] == "type_based":
            title = f"{pattern['feedback_type']} 관련 이슈 개선 필요"
        else:
            title = f"{improvement_type.value} 개선 필요"

        # 설명 생성
        description = f"패턴 분석 결과: {pattern['description']}\n"
        if "count" in pattern:
            description += f"발생 빈도: {pattern['count']}회\n"
        if "anomaly_count" in pattern:
            description += f"이상치 수: {pattern['anomaly_count']}개\n"

        # 예상 이점 추정
        expected_benefits = {
            "confidence": confidence,
            "significance": significance
        }
        if improvement_type == ImprovementType.PERFORMANCE:
            expected_benefits["performance_improvement"] = 0.3
        elif improvement_type == ImprovementType.RESOURCE:
            expected_benefits["resource_saving"] = 0.25
        elif improvement_type == ImprovementType.RELIABILITY:
            expected_benefits["reliability_improvement"] = 0.4

        # 구현 비용 추정
        implementation_cost = {
            "development_time": 0.5,  # 중간 정도의 개발 시간
            "resource_requirement": 0.3,  # 낮은 리소스 요구사항
            "risk_level": 0.2  # 낮은 위험도
        }

        return ImprovementSuggestion(
            id=suggestion_id,
            type=improvement_type,
            title=title,
            description=description,
            priority=significance,
            related_feedbacks=related_feedbacks,
            metrics=pattern.get("metrics", {}),
            expected_benefits=expected_benefits,
            implementation_cost=implementation_cost,
            tags=[improvement_type.value, pattern["type"]]
        )
