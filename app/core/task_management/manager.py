"""작업 관리 시스템의 핵심 관리자 클래스"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import uuid

from .models import Task, SimpleTask, ComplexTask, TaskStatus, TaskDependency

class TaskManager:
    """작업 관리자 클래스"""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_dependencies: Dict[str, List[TaskDependency]] = {}
        self._lock = asyncio.Lock()

    def generate_task_id(self) -> str:
        """고유한 작업 ID 생성"""
        return str(uuid.uuid4())

    async def create_task(self, description: str, dependencies: List[TaskDependency] = None) -> Task:
        """새로운 작업 생성"""
        task_id = self.generate_task_id()
        task = Task(
            id=task_id,
            description=description,
            status=TaskStatus.PENDING,
            dependencies=dependencies or [],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={}
        )

        async with self._lock:
            self.tasks[task_id] = task
            self.task_dependencies[task_id] = dependencies or []

        return task

    async def decompose_task(self, complex_task: ComplexTask) -> List[SimpleTask]:
        """복잡한 작업을 단순 작업들로 분해"""
        subtasks = []
        for i, subtask_spec in enumerate(complex_task.subtasks):
            simple_task = SimpleTask(
                id=self.generate_task_id(),
                description=subtask_spec.description,
                status=TaskStatus.PENDING,
                dependencies=subtask_spec.dependencies,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata=subtask_spec.metadata,
                parent_id=complex_task.id,
                execution_order=i
            )
            subtasks.append(simple_task)

            async with self._lock:
                self.tasks[simple_task.id] = simple_task
                self.task_dependencies[simple_task.id] = simple_task.dependencies

        return subtasks

    async def get_task(self, task_id: str) -> Optional[Task]:
        """작업 정보 조회"""
        return self.tasks.get(task_id)

    async def update_task_status(self, task_id: str, status: TaskStatus, progress: float = None) -> None:
        """작업 상태 업데이트"""
        async with self._lock:
            if task := self.tasks.get(task_id):
                task.status = status
                task.updated_at = datetime.now()
                if progress is not None:
                    task.progress = progress

    async def get_ready_tasks(self) -> List[Task]:
        """실행 가능한 작업 목록 조회"""
        ready_tasks = []
        async with self._lock:
            for task_id, task in self.tasks.items():
                if task.status == TaskStatus.PENDING and await self._are_dependencies_met(task_id):
                    ready_tasks.append(task)
        return ready_tasks

    async def _are_dependencies_met(self, task_id: str) -> bool:
        """작업의 의존성이 모두 충족되었는지 확인"""
        dependencies = self.task_dependencies.get(task_id, [])
        for dep in dependencies:
            if dep.required:
                dependent_task = self.tasks.get(dep.task_id)
                if not dependent_task or dependent_task.status != TaskStatus.COMPLETED:
                    return False
        return True
