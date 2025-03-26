"""
피드백 시스템의 데이터 모델을 정의하는 모듈입니다.
이 모듈은 피드백 데이터의 구조와 관련 열거형을 포함합니다.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field

class FeedbackType(str, Enum):
    """피드백 유형을 정의하는 열거형"""

    EXECUTION = "execution"  # 실행 관련 피드백
    PERFORMANCE = "performance"  # 성능 관련 피드백
    USABILITY = "usability"  # 사용성 관련 피드백
    ERROR = "error"  # 오류 관련 피드백
    SUGGESTION = "suggestion"  # 개선 제안
    OTHER = "other"  # 기타 피드백

class FeedbackSeverity(str, Enum):
    """피드백 중요도를 정의하는 열거형"""

    LOW = "low"  # 낮은 중요도
    MEDIUM = "medium"  # 중간 중요도
    HIGH = "high"  # 높은 중요도
    CRITICAL = "critical"  # 매우 높은 중요도

class FeedbackStatus(str, Enum):
    """피드백 상태를 정의하는 열거형"""

    NEW = "new"  # 새로운 피드백
    IN_REVIEW = "in_review"  # 검토 중
    ACCEPTED = "accepted"  # 수락됨
    REJECTED = "rejected"  # 거부됨
    IMPLEMENTED = "implemented"  # 구현됨
    CLOSED = "closed"  # 종료됨

class Feedback(BaseModel):
    """피드백 데이터 모델"""

    id: str = Field(description="피드백의 고유 식별자")
    plan_id: str = Field(description="관련 계획의 ID")
    type: FeedbackType = Field(description="피드백 유형")
    severity: FeedbackSeverity = Field(description="피드백 중요도")
    status: FeedbackStatus = Field(default=FeedbackStatus.NEW, description="피드백 상태")

    title: str = Field(description="피드백 제목")
    description: str = Field(description="피드백 상세 내용")

    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.now, description="최종 수정 시간")

    step_index: Optional[int] = Field(default=None, description="관련 계획 단계 인덱스")
    metrics: Dict[str, Union[str, int, float]] = Field(
        default_factory=dict,
        description="관련 메트릭 데이터"
    )
    tags: List[str] = Field(default_factory=list, description="피드백 태그")

    def update_status(self, new_status: FeedbackStatus) -> None:
        """피드백 상태 업데이트"""
        self.status = new_status
        self.updated_at = datetime.now()

    def add_metric(self, key: str, value: Union[str, int, float]) -> None:
        """메트릭 추가"""
        self.metrics[key] = value
        self.updated_at = datetime.now()

    def add_tag(self, tag: str) -> None:
        """태그 추가"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        """피드백을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "type": self.type.value,
            "severity": self.severity.value,
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "step_index": self.step_index,
            "metrics": self.metrics,
            "tags": self.tags
        }

class ImprovementType(Enum):
    """개선사항 유형을 정의하는 열거형"""
    PERFORMANCE = "performance"  # 성능 개선
    RESOURCE = "resource"       # 리소스 사용 최적화
    RELIABILITY = "reliability" # 안정성 향상
    EFFICIENCY = "efficiency"   # 효율성 개선
    STRATEGY = "strategy"       # 전략적 개선

class ImprovementStatus(Enum):
    """개선사항 상태를 정의하는 열거형"""
    PROPOSED = "proposed"       # 제안됨
    UNDER_REVIEW = "under_review" # 검토 중
    APPROVED = "approved"       # 승인됨
    IMPLEMENTING = "implementing" # 구현 중
    IMPLEMENTED = "implemented" # 구현됨
    REJECTED = "rejected"       # 거부됨

class ImprovementSuggestion:
    """
    개선사항 제안을 나타내는 클래스입니다.

    Attributes:
        id (str): 개선사항의 고유 식별자
        type (ImprovementType): 개선사항의 유형
        title (str): 개선사항의 제목
        description (str): 개선사항의 상세 설명
        status (ImprovementStatus): 개선사항의 현재 상태
        priority (float): 개선사항의 우선순위 (0.0 ~ 1.0)
        created_at (datetime): 개선사항이 생성된 시간
        updated_at (datetime): 개선사항이 마지막으로 수정된 시간
        related_feedbacks (List[str]): 관련된 피드백들의 ID 목록
        metrics (Dict): 개선사항과 관련된 메트릭
        expected_benefits (Dict): 예상되는 이점
        implementation_cost (Dict): 구현 비용 추정
        tags (List[str]): 개선사항과 관련된 태그들
    """

    def __init__(
        self,
        id: str,
        type: ImprovementType,
        title: str,
        description: str,
        priority: float,
        related_feedbacks: Optional[List[str]] = None,
        metrics: Optional[Dict] = None,
        expected_benefits: Optional[Dict] = None,
        implementation_cost: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ):
        """
        ImprovementSuggestion 객체를 초기화합니다.

        Args:
            id: 개선사항의 고유 식별자
            type: 개선사항의 유형
            title: 개선사항의 제목
            description: 개선사항의 상세 설명
            priority: 개선사항의 우선순위 (0.0 ~ 1.0)
            related_feedbacks: 관련된 피드백들의 ID 목록
            metrics: 개선사항과 관련된 메트릭
            expected_benefits: 예상되는 이점
            implementation_cost: 구현 비용 추정
            tags: 개선사항과 관련된 태그들
        """
        self.id = id
        self.type = type
        self.title = title
        self.description = description
        self.status = ImprovementStatus.PROPOSED
        self.priority = max(0.0, min(1.0, priority))  # 0.0 ~ 1.0 범위로 제한
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.related_feedbacks = related_feedbacks or []
        self.metrics = metrics or {}
        self.expected_benefits = expected_benefits or {}
        self.implementation_cost = implementation_cost or {}
        self.tags = tags or []

    def update_status(self, new_status: ImprovementStatus) -> None:
        """
        개선사항의 상태를 업데이트합니다.

        Args:
            new_status: 새로운 상태
        """
        self.status = new_status
        self.updated_at = datetime.now()

    def update_priority(self, new_priority: float) -> None:
        """
        개선사항의 우선순위를 업데이트합니다.

        Args:
            new_priority: 새로운 우선순위 (0.0 ~ 1.0)
        """
        self.priority = max(0.0, min(1.0, new_priority))
        self.updated_at = datetime.now()

    def add_related_feedback(self, feedback_id: str) -> None:
        """
        관련된 피드백을 추가합니다.

        Args:
            feedback_id: 추가할 피드백의 ID
        """
        if feedback_id not in self.related_feedbacks:
            self.related_feedbacks.append(feedback_id)
            self.updated_at = datetime.now()

    def update_metrics(self, metrics: Dict) -> None:
        """
        메트릭을 업데이트합니다.

        Args:
            metrics: 업데이트할 메트릭
        """
        self.metrics.update(metrics)
        self.updated_at = datetime.now()

    def update_expected_benefits(self, benefits: Dict) -> None:
        """
        예상되는 이점을 업데이트합니다.

        Args:
            benefits: 업데이트할 이점
        """
        self.expected_benefits.update(benefits)
        self.updated_at = datetime.now()

    def update_implementation_cost(self, cost: Dict) -> None:
        """
        구현 비용 추정을 업데이트합니다.

        Args:
            cost: 업데이트할 비용 추정
        """
        self.implementation_cost.update(cost)
        self.updated_at = datetime.now()

    def add_tags(self, tags: List[str]) -> None:
        """
        태그를 추가합니다.

        Args:
            tags: 추가할 태그 목록
        """
        for tag in tags:
            if tag not in self.tags:
                self.tags.append(tag)
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        """
        개선사항을 딕셔너리로 변환합니다.

        Returns:
            Dict: 개선사항의 딕셔너리 표현
        """
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "related_feedbacks": self.related_feedbacks,
            "metrics": self.metrics,
            "expected_benefits": self.expected_benefits,
            "implementation_cost": self.implementation_cost,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ImprovementSuggestion':
        """
        딕셔너리로부터 개선사항 객체를 생성합니다.

        Args:
            data: 개선사항 데이터를 담은 딕셔너리

        Returns:
            ImprovementSuggestion: 생성된 개선사항 객체
        """
        suggestion = cls(
            id=data["id"],
            type=ImprovementType(data["type"]),
            title=data["title"],
            description=data["description"],
            priority=data["priority"],
            related_feedbacks=data.get("related_feedbacks", []),
            metrics=data.get("metrics", {}),
            expected_benefits=data.get("expected_benefits", {}),
            implementation_cost=data.get("implementation_cost", {}),
            tags=data.get("tags", [])
        )
        suggestion.status = ImprovementStatus(data["status"])
        suggestion.created_at = datetime.fromisoformat(data["created_at"])
        suggestion.updated_at = datetime.fromisoformat(data["updated_at"])
        return suggestion
