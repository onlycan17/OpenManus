"""작업 관리를 위한 기본 모델 정의"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime

class TaskStatus(Enum):
    """작업 상태를 나타내는 열거형"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class TaskDependency:
    """작업 의존성 정보"""
    task_id: str
    dependency_type: str
    required: bool = True

@dataclass
class Task:
    """기본 작업 클래스"""
    id: str
    description: str
    status: TaskStatus
    dependencies: List[TaskDependency]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    error: Optional[Exception] = None
    progress: float = 0.0

@dataclass
class ComplexTask(Task):
    """복잡한 작업을 나타내는 클래스"""
    subtasks: List[Task]
    completion_criteria: Dict[str, Any]

@dataclass
class SimpleTask(Task):
    """단순 작업을 나타내는 클래스"""
    parent_id: Optional[str] = None
    execution_order: int = 0
