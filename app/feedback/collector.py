"""
피드백 수집 기능을 구현하는 모듈입니다.
이 모듈은 피드백 데이터를 수집하고 저장하는 기능을 제공합니다.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union

from app.feedback.models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    FeedbackStatus
)

class FeedbackCollector:
    """피드백 수집기 클래스"""

    def __init__(self):
        self._feedbacks: Dict[str, Feedback] = {}

    def create_feedback(
        self,
        plan_id: str,
        type: FeedbackType,
        severity: FeedbackSeverity,
        title: str,
        description: str,
        step_index: Optional[int] = None,
        metrics: Optional[Dict[str, Union[str, int, float]]] = None,
        tags: Optional[List[str]] = None
    ) -> Feedback:
        """새로운 피드백 생성"""
        feedback_id = str(uuid.uuid4())

        feedback = Feedback(
            id=feedback_id,
            plan_id=plan_id,
            type=type,
            severity=severity,
            title=title,
            description=description,
            step_index=step_index,
            metrics=metrics or {},
            tags=tags or []
        )

        self._feedbacks[feedback_id] = feedback
        return feedback

    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """피드백 조회"""
        return self._feedbacks.get(feedback_id)

    def get_feedbacks_by_plan(self, plan_id: str) -> List[Feedback]:
        """특정 계획의 모든 피드백 조회"""
        return [
            feedback for feedback in self._feedbacks.values()
            if feedback.plan_id == plan_id
        ]

    def get_feedbacks_by_type(self, type: FeedbackType) -> List[Feedback]:
        """특정 유형의 모든 피드백 조회"""
        return [
            feedback for feedback in self._feedbacks.values()
            if feedback.type == type
        ]

    def get_feedbacks_by_severity(self, severity: FeedbackSeverity) -> List[Feedback]:
        """특정 중요도의 모든 피드백 조회"""
        return [
            feedback for feedback in self._feedbacks.values()
            if feedback.severity == severity
        ]

    def update_feedback_status(
        self,
        feedback_id: str,
        new_status: FeedbackStatus
    ) -> Optional[Feedback]:
        """피드백 상태 업데이트"""
        feedback = self._feedbacks.get(feedback_id)
        if feedback:
            feedback.update_status(new_status)
            return feedback
        return None

    def add_feedback_metric(
        self,
        feedback_id: str,
        key: str,
        value: Union[str, int, float]
    ) -> Optional[Feedback]:
        """피드백 메트릭 추가"""
        feedback = self._feedbacks.get(feedback_id)
        if feedback:
            feedback.add_metric(key, value)
            return feedback
        return None

    def add_feedback_tag(
        self,
        feedback_id: str,
        tag: str
    ) -> Optional[Feedback]:
        """피드백 태그 추가"""
        feedback = self._feedbacks.get(feedback_id)
        if feedback:
            feedback.add_tag(tag)
            return feedback
        return None

    def delete_feedback(self, feedback_id: str) -> bool:
        """피드백 삭제"""
        if feedback_id in self._feedbacks:
            del self._feedbacks[feedback_id]
            return True
        return False

    def get_all_feedbacks(self) -> List[Feedback]:
        """모든 피드백 조회"""
        return list(self._feedbacks.values())

    def get_feedback_count(self) -> int:
        """전체 피드백 수 조회"""
        return len(self._feedbacks)

    def clear_feedbacks(self) -> None:
        """모든 피드백 삭제"""
        self._feedbacks.clear()
