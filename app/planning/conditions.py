"""
계획의 조건부 실행 로직을 구현하는 모듈입니다.
이 모듈은 다양한 유형의 조건 평가와 조건부 실행을 지원합니다.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class ConditionType(str, Enum):
    """조건 유형을 정의하는 열거형"""

    RESOURCE = "resource"  # 리소스 관련 조건
    DEPENDENCY = "dependency"  # 의존성 관련 조건
    TIME = "time"  # 시간 관련 조건
    STATUS = "status"  # 상태 관련 조건
    CUSTOM = "custom"  # 사용자 정의 조건

class ConditionOperator(str, Enum):
    """조건 연산자를 정의하는 열거형"""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUALS = "greater_equals"
    LESS_EQUALS = "less_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"

class ConditionContext(BaseModel):
    """조건 평가에 필요한 컨텍스트 정보"""

    resources: Dict[str, Any] = Field(default_factory=dict, description="사용 가능한 리소스 정보")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="의존성 상태 정보")
    current_time: datetime = Field(default_factory=datetime.now, description="현재 시간")
    status: Dict[str, Any] = Field(default_factory=dict, description="현재 상태 정보")
    custom_data: Dict[str, Any] = Field(default_factory=dict, description="사용자 정의 데이터")

class ConditionEvaluator:
    """조건 평가를 수행하는 클래스"""

    @staticmethod
    def evaluate_equals(value: Any, target: Any) -> bool:
        """equals 연산자 평가"""
        return value == target

    @staticmethod
    def evaluate_not_equals(value: Any, target: Any) -> bool:
        """not_equals 연산자 평가"""
        return value != target

    @staticmethod
    def evaluate_greater_than(value: Any, target: Any) -> bool:
        """greater_than 연산자 평가"""
        return value > target

    @staticmethod
    def evaluate_less_than(value: Any, target: Any) -> bool:
        """less_than 연산자 평가"""
        return value < target

    @staticmethod
    def evaluate_greater_equals(value: Any, target: Any) -> bool:
        """greater_equals 연산자 평가"""
        return value >= target

    @staticmethod
    def evaluate_less_equals(value: Any, target: Any) -> bool:
        """less_equals 연산자 평가"""
        return value <= target

    @staticmethod
    def evaluate_contains(value: Any, target: Any) -> bool:
        """contains 연산자 평가"""
        return target in value

    @staticmethod
    def evaluate_not_contains(value: Any, target: Any) -> bool:
        """not_contains 연산자 평가"""
        return target not in value

    @staticmethod
    def evaluate_in(value: Any, target: Any) -> bool:
        """in 연산자 평가"""
        return value in target

    @staticmethod
    def evaluate_not_in(value: Any, target: Any) -> bool:
        """not_in 연산자 평가"""
        return value not in target

class ConditionHandler:
    """조건 처리를 담당하는 클래스"""

    def __init__(self):
        self.evaluator = ConditionEvaluator()
        self._operator_map = {
            ConditionOperator.EQUALS: self.evaluator.evaluate_equals,
            ConditionOperator.NOT_EQUALS: self.evaluator.evaluate_not_equals,
            ConditionOperator.GREATER_THAN: self.evaluator.evaluate_greater_than,
            ConditionOperator.LESS_THAN: self.evaluator.evaluate_less_than,
            ConditionOperator.GREATER_EQUALS: self.evaluator.evaluate_greater_equals,
            ConditionOperator.LESS_EQUALS: self.evaluator.evaluate_less_equals,
            ConditionOperator.CONTAINS: self.evaluator.evaluate_contains,
            ConditionOperator.NOT_CONTAINS: self.evaluator.evaluate_not_contains,
            ConditionOperator.IN: self.evaluator.evaluate_in,
            ConditionOperator.NOT_IN: self.evaluator.evaluate_not_in,
        }

    def evaluate_condition(
        self,
        condition_type: ConditionType,
        operator: ConditionOperator,
        value: Any,
        context: ConditionContext
    ) -> bool:
        """조건 평가"""
        try:
            # 컨텍스트에서 적절한 값 추출
            if condition_type == ConditionType.RESOURCE:
                target = context.resources.get(str(value))
            elif condition_type == ConditionType.DEPENDENCY:
                target = context.dependencies.get(str(value))
            elif condition_type == ConditionType.TIME:
                target = context.current_time
            elif condition_type == ConditionType.STATUS:
                target = context.status.get(str(value))
            elif condition_type == ConditionType.CUSTOM:
                target = context.custom_data.get(str(value))
            else:
                raise ValueError(f"Unknown condition type: {condition_type}")

            # 해당하는 연산자로 평가 수행
            evaluate_func = self._operator_map.get(operator)
            if not evaluate_func:
                raise ValueError(f"Unknown operator: {operator}")

            return evaluate_func(value, target)

        except Exception as e:
            # 평가 중 오류 발생 시 False 반환
            return False

    def evaluate_conditions(
        self,
        conditions: List[Dict[str, Any]],
        context: ConditionContext
    ) -> bool:
        """여러 조건 평가"""
        # 조건이 없으면 True 반환
        if not conditions:
            return True

        # 모든 조건이 만족되어야 True 반환 (AND 로직)
        return all(
            self.evaluate_condition(
                ConditionType(condition["type"]),
                ConditionOperator(condition["operator"]),
                condition["value"],
                context
            )
            for condition in conditions
        )
