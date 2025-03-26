"""
향상된 계획 도구를 구현하는 모듈입니다.
이 모듈은 계층적 계획 구조와 조건부 실행을 지원하는 도구를 제공합니다.
"""

from typing import Dict, List, Optional
from datetime import datetime

from app.exceptions import ToolError
from app.tool.base import BaseTool, ToolResult
from app.planning.hierarchical import HierarchicalPlan, PlanCondition
from app.planning.conditions import ConditionContext, ConditionHandler

class EnhancedPlanningTool(BaseTool):
    """
    향상된 계획 도구 클래스.
    계층적 계획 구조와 조건부 실행을 지원합니다.
    """

    name: str = "enhanced_planning"
    description: str = "Enhanced planning tool with hierarchical structure and conditional execution support"
    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "The command to execute",
                "enum": [
                    "create",
                    "create_subplan",
                    "update",
                    "list",
                    "get",
                    "set_active",
                    "mark_step",
                    "add_condition",
                    "add_fallback",
                    "evaluate_conditions",
                    "delete",
                ],
                "type": "string",
            },
            "plan_id": {
                "description": "Unique identifier for the plan",
                "type": "string",
            },
            "parent_id": {
                "description": "Parent plan ID for subplan creation",
                "type": "string",
            },
            "title": {
                "description": "Title for the plan",
                "type": "string",
            },
            "description": {
                "description": "Description of the plan",
                "type": "string",
            },
            "steps": {
                "description": "List of plan steps",
                "type": "array",
                "items": {"type": "string"},
            },
            "step_index": {
                "description": "Index of the step to update",
                "type": "integer",
            },
            "step_status": {
                "description": "Status to set for a step",
                "enum": ["not_started", "in_progress", "completed", "blocked"],
                "type": "string",
            },
            "step_note": {
                "description": "Note to add to a step",
                "type": "string",
            },
            "condition": {
                "description": "Condition to add to the plan",
                "type": "object",
            },
            "fallback_id": {
                "description": "ID of the fallback plan to add",
                "type": "string",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    }

    # 계획 저장소
    plans: Dict[str, HierarchicalPlan] = {}
    _current_plan_id: Optional[str] = None

    def __init__(self):
        super().__init__()
        self.condition_handler = ConditionHandler()

    async def execute(
        self,
        *,
        command: str,
        plan_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        steps: Optional[List[str]] = None,
        step_index: Optional[int] = None,
        step_status: Optional[str] = None,
        step_note: Optional[str] = None,
        condition: Optional[Dict] = None,
        fallback_id: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """도구 실행"""

        if command == "create":
            return await self._create_plan(plan_id, title, description, steps)
        elif command == "create_subplan":
            return await self._create_subplan(plan_id, parent_id, title, description, steps)
        elif command == "update":
            return await self._update_plan(plan_id, title, description, steps)
        elif command == "list":
            return await self._list_plans()
        elif command == "get":
            return await self._get_plan(plan_id)
        elif command == "set_active":
            return await self._set_active_plan(plan_id)
        elif command == "mark_step":
            return await self._mark_step(plan_id, step_index, step_status, step_note)
        elif command == "add_condition":
            return await self._add_condition(plan_id, condition)
        elif command == "add_fallback":
            return await self._add_fallback(plan_id, fallback_id)
        elif command == "evaluate_conditions":
            return await self._evaluate_conditions(plan_id)
        elif command == "delete":
            return await self._delete_plan(plan_id)
        else:
            raise ToolError(f"Unknown command: {command}")

    async def _create_plan(
        self,
        plan_id: Optional[str],
        title: Optional[str],
        description: Optional[str],
        steps: Optional[List[str]],
    ) -> ToolResult:
        """새로운 계획 생성"""
        if not plan_id:
            raise ToolError("plan_id is required")
        if not title:
            raise ToolError("title is required")
        if not steps:
            raise ToolError("steps is required")

        if plan_id in self.plans:
            raise ToolError(f"Plan {plan_id} already exists")

        plan = HierarchicalPlan(
            id=plan_id,
            title=title,
            description=description,
            steps=steps,
        )
        self.plans[plan_id] = plan
        self._current_plan_id = plan_id

        return ToolResult(output=f"Created plan: {plan_id}\n\n{plan.to_dict()}")

    async def _create_subplan(
        self,
        plan_id: Optional[str],
        parent_id: Optional[str],
        title: Optional[str],
        description: Optional[str],
        steps: Optional[List[str]],
    ) -> ToolResult:
        """하위 계획 생성"""
        if not plan_id or not parent_id:
            raise ToolError("Both plan_id and parent_id are required")
        if not title or not steps:
            raise ToolError("Both title and steps are required")

        if plan_id in self.plans:
            raise ToolError(f"Plan {plan_id} already exists")
        if parent_id not in self.plans:
            raise ToolError(f"Parent plan {parent_id} does not exist")

        plan = HierarchicalPlan(
            id=plan_id,
            title=title,
            description=description,
            steps=steps,
            parent_id=parent_id,
        )
        self.plans[plan_id] = plan
        self.plans[parent_id].add_child(plan_id)

        return ToolResult(
            output=f"Created subplan: {plan_id} under parent: {parent_id}\n\n{plan.to_dict()}"
        )

    async def _update_plan(
        self,
        plan_id: Optional[str],
        title: Optional[str],
        description: Optional[str],
        steps: Optional[List[str]],
    ) -> ToolResult:
        """계획 업데이트"""
        if not plan_id:
            raise ToolError("plan_id is required")

        plan = self._get_plan_or_error(plan_id)

        if title:
            plan.title = title
        if description:
            plan.description = description
        if steps:
            plan.steps = steps
            plan.step_statuses = ["not_started"] * len(steps)
            plan.step_notes = [""] * len(steps)

        return ToolResult(output=f"Updated plan: {plan_id}\n\n{plan.to_dict()}")

    async def _list_plans(self) -> ToolResult:
        """계획 목록 조회"""
        if not self.plans:
            return ToolResult(output="No plans available")

        output = "Available plans:\n"
        for plan_id, plan in self.plans.items():
            current = " (current)" if plan_id == self._current_plan_id else ""
            parent = f" (parent: {plan.parent_id})" if plan.parent_id else ""
            children = f" (children: {len(plan.child_ids)})" if plan.child_ids else ""
            output += f"- {plan_id}{current}{parent}{children}: {plan.title}\n"

        return ToolResult(output=output)

    async def _get_plan(self, plan_id: Optional[str]) -> ToolResult:
        """계획 조회"""
        if not plan_id:
            if not self._current_plan_id:
                raise ToolError("No active plan")
            plan_id = self._current_plan_id

        plan = self._get_plan_or_error(plan_id)
        return ToolResult(output=str(plan.to_dict()))

    async def _set_active_plan(self, plan_id: Optional[str]) -> ToolResult:
        """활성 계획 설정"""
        if not plan_id:
            raise ToolError("plan_id is required")

        if plan_id not in self.plans:
            raise ToolError(f"Plan {plan_id} does not exist")

        self._current_plan_id = plan_id
        return ToolResult(output=f"Set active plan to: {plan_id}")

    async def _mark_step(
        self,
        plan_id: Optional[str],
        step_index: Optional[int],
        step_status: Optional[str],
        step_note: Optional[str],
    ) -> ToolResult:
        """단계 상태 및 노트 설정"""
        if not plan_id:
            if not self._current_plan_id:
                raise ToolError("No active plan")
            plan_id = self._current_plan_id

        plan = self._get_plan_or_error(plan_id)

        if step_index is None:
            raise ToolError("step_index is required")

        if step_status:
            plan.set_step_status(step_index, step_status)
        if step_note:
            plan.add_step_note(step_index, step_note)

        return ToolResult(
            output=f"Updated step {step_index} in plan {plan_id}\n\n{plan.to_dict()}"
        )

    async def _add_condition(
        self,
        plan_id: Optional[str],
        condition: Optional[Dict],
    ) -> ToolResult:
        """조건 추가"""
        if not plan_id:
            if not self._current_plan_id:
                raise ToolError("No active plan")
            plan_id = self._current_plan_id

        if not condition:
            raise ToolError("condition is required")

        plan = self._get_plan_or_error(plan_id)
        plan.add_condition(PlanCondition(**condition))

        return ToolResult(
            output=f"Added condition to plan {plan_id}\n\n{plan.to_dict()}"
        )

    async def _add_fallback(
        self,
        plan_id: Optional[str],
        fallback_id: Optional[str],
    ) -> ToolResult:
        """대체 계획 추가"""
        if not plan_id:
            if not self._current_plan_id:
                raise ToolError("No active plan")
            plan_id = self._current_plan_id

        if not fallback_id:
            raise ToolError("fallback_id is required")

        plan = self._get_plan_or_error(plan_id)
        if fallback_id not in self.plans:
            raise ToolError(f"Fallback plan {fallback_id} does not exist")

        plan.add_fallback(fallback_id)

        return ToolResult(
            output=f"Added fallback plan {fallback_id} to plan {plan_id}\n\n{plan.to_dict()}"
        )

    async def _evaluate_conditions(self, plan_id: Optional[str]) -> ToolResult:
        """조건 평가"""
        if not plan_id:
            if not self._current_plan_id:
                raise ToolError("No active plan")
            plan_id = self._current_plan_id

        plan = self._get_plan_or_error(plan_id)

        # 기본 컨텍스트 생성
        context = ConditionContext(
            current_time=datetime.now(),
            # 필요한 경우 다른 컨텍스트 정보 추가
        )

        # 조건 평가
        conditions = [condition.dict() for condition in plan.conditions]
        result = self.condition_handler.evaluate_conditions(conditions, context)

        return ToolResult(
            output=f"Conditions evaluation for plan {plan_id}: {'Pass' if result else 'Fail'}"
        )

    async def _delete_plan(self, plan_id: Optional[str]) -> ToolResult:
        """계획 삭제"""
        if not plan_id:
            raise ToolError("plan_id is required")

        if plan_id not in self.plans:
            raise ToolError(f"Plan {plan_id} does not exist")

        # 하위 계획이 있는 경우 함께 삭제
        plan = self.plans[plan_id]
        for child_id in plan.child_ids:
            if child_id in self.plans:
                del self.plans[child_id]

        # 부모 계획이 있는 경우 자식 목록에서 제거
        if plan.parent_id and plan.parent_id in self.plans:
            parent = self.plans[plan.parent_id]
            if plan_id in parent.child_ids:
                parent.child_ids.remove(plan_id)

        del self.plans[plan_id]

        # 현재 활성 계획인 경우 초기화
        if self._current_plan_id == plan_id:
            self._current_plan_id = None

        return ToolResult(output=f"Deleted plan: {plan_id}")

    def _get_plan_or_error(self, plan_id: str) -> HierarchicalPlan:
        """계획 조회 또는 에러"""
        if plan_id not in self.plans:
            raise ToolError(f"Plan {plan_id} does not exist")
        return self.plans[plan_id]
