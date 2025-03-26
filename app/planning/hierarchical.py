"""
계층적 계획 구조를 구현하는 모듈입니다.
이 모듈은 계획의 계층 구조, 조건부 실행, 대체 계획 등을 지원합니다.
"""

from typing import Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

class PlanCondition(BaseModel):
    """계획 실행 조건을 정의하는 클래스"""

    type: str = Field(description="조건의 유형 (resource, dependency, time 등)")
    operator: str = Field(description="조건 연산자 (equals, greater_than, less_than 등)")
    value: Union[str, int, float, bool] = Field(description="조건 값")
    description: Optional[str] = Field(default=None, description="조건에 대한 설명")

class ExecutionStats(BaseModel):
    """계획 실행 통계를 추적하는 클래스"""

    success_count: int = Field(default=0, description="성공한 실행 횟수")
    failure_count: int = Field(default=0, description="실패한 실행 횟수")
    total_duration: float = Field(default=0.0, description="총 실행 시간")
    last_execution: Optional[datetime] = Field(default=None, description="마지막 실행 시간")
    failure_reasons: List[str] = Field(default_factory=list, description="실패 이유 목록")

    @property
    def success_rate(self) -> float:
        """성공률 계산"""
        total = self.success_count + self.failure_count
        return (self.success_count / total) * 100 if total > 0 else 0.0

    @property
    def average_duration(self) -> float:
        """평균 실행 시간 계산"""
        total = self.success_count + self.failure_count
        return self.total_duration / total if total > 0 else 0.0

class HierarchicalPlan(BaseModel):
    """계층적 계획을 구현하는 클래스"""

    id: str = Field(description="계획의 고유 식별자")
    title: str = Field(description="계획의 제목")
    description: Optional[str] = Field(default=None, description="계획에 대한 설명")

    # 계층 구조
    parent_id: Optional[str] = Field(default=None, description="부모 계획의 ID")
    child_ids: List[str] = Field(default_factory=list, description="자식 계획들의 ID 목록")

    # 계획 내용
    steps: List[str] = Field(default_factory=list, description="실행할 단계들")
    step_statuses: List[str] = Field(default_factory=list, description="각 단계의 상태")
    step_notes: List[str] = Field(default_factory=list, description="각 단계에 대한 노트")

    # 실행 조건 및 대체 계획
    conditions: List[PlanCondition] = Field(default_factory=list, description="실행 조건들")
    fallback_plan_ids: List[str] = Field(default_factory=list, description="대체 계획들의 ID")

    # 실행 통계
    execution_stats: ExecutionStats = Field(default_factory=ExecutionStats, description="실행 통계")

    def add_child(self, child_id: str) -> None:
        """자식 계획 추가"""
        if child_id not in self.child_ids:
            self.child_ids.append(child_id)

    def add_condition(self, condition: PlanCondition) -> None:
        """실행 조건 추가"""
        self.conditions.append(condition)

    def add_fallback(self, fallback_id: str) -> None:
        """대체 계획 추가"""
        if fallback_id not in self.fallback_plan_ids:
            self.fallback_plan_ids.append(fallback_id)

    def update_execution_stats(self, success: bool, duration: float, failure_reason: Optional[str] = None) -> None:
        """실행 통계 업데이트"""
        if success:
            self.execution_stats.success_count += 1
        else:
            self.execution_stats.failure_count += 1
            if failure_reason:
                self.execution_stats.failure_reasons.append(failure_reason)

        self.execution_stats.total_duration += duration
        self.execution_stats.last_execution = datetime.now()

    def get_step_status(self, step_index: int) -> str:
        """특정 단계의 상태 조회"""
        if 0 <= step_index < len(self.step_statuses):
            return self.step_statuses[step_index]
        raise IndexError(f"Step index {step_index} is out of range")

    def set_step_status(self, step_index: int, status: str) -> None:
        """특정 단계의 상태 설정"""
        if 0 <= step_index < len(self.steps):
            while len(self.step_statuses) <= step_index:
                self.step_statuses.append("not_started")
            self.step_statuses[step_index] = status
        else:
            raise IndexError(f"Step index {step_index} is out of range")

    def add_step_note(self, step_index: int, note: str) -> None:
        """특정 단계에 노트 추가"""
        if 0 <= step_index < len(self.steps):
            while len(self.step_notes) <= step_index:
                self.step_notes.append("")
            self.step_notes[step_index] = note
        else:
            raise IndexError(f"Step index {step_index} is out of range")

    def to_dict(self) -> Dict:
        """계획을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "parent_id": self.parent_id,
            "child_ids": self.child_ids,
            "steps": self.steps,
            "step_statuses": self.step_statuses,
            "step_notes": self.step_notes,
            "conditions": [condition.dict() for condition in self.conditions],
            "fallback_plan_ids": self.fallback_plan_ids,
            "execution_stats": self.execution_stats.dict()
        }
