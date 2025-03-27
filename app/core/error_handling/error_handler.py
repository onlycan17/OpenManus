"""오류 처리 및 복구 시스템"""

import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RetryPolicy:
    """재시도 정책 클래스"""

    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.attempt_count: Dict[str, int] = {}

    def should_retry(self, task_id: str, error: Exception) -> bool:
        """재시도 여부 결정"""
        current_attempts = self.attempt_count.get(task_id, 0)
        return current_attempts < self.max_attempts

    def get_delay(self, attempt: int) -> float:
        """재시도 대기 시간 계산 (지수 백오프)"""
        return self.base_delay * (2 ** attempt)

    def record_attempt(self, task_id: str) -> None:
        """재시도 횟수 기록"""
        self.attempt_count[task_id] = self.attempt_count.get(task_id, 0) + 1

    def reset(self, task_id: str) -> None:
        """재시도 횟수 초기화"""
        self.attempt_count.pop(task_id, None)

class ErrorHandler:
    """오류 처리 관리자 클래스"""

    def __init__(self):
        self.retry_policy = RetryPolicy()
        self.error_callbacks: Dict[str, List[Callable]] = {}
        self.error_history: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def handle_error(self, task_id: str, error: Exception) -> bool:
        """오류 처리"""
        await self._log_error(task_id, error)

        if self.retry_policy.should_retry(task_id, error):
            self.retry_policy.record_attempt(task_id)
            return True  # 재시도 가능

        await self._execute_error_callbacks(task_id, error)
        return False  # 재시도 불가

    async def _log_error(self, task_id: str, error: Exception) -> None:
        """오류 로깅"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'task_id': task_id
        }

        async with self._lock:
            if task_id not in self.error_history:
                self.error_history[task_id] = []
            self.error_history[task_id].append(error_info)

        logger.error(f"Task {task_id} failed: {str(error)}", exc_info=True)

    async def _execute_error_callbacks(self, task_id: str, error: Exception) -> None:
        """오류 콜백 실행"""
        callbacks = self.error_callbacks.get(task_id, [])
        for callback in callbacks:
            try:
                await callback(error)
            except Exception as e:
                logger.error(f"Error callback failed: {str(e)}", exc_info=True)

    def register_error_callback(self, task_id: str, callback: Callable) -> None:
        """오류 처리 콜백 등록"""
        if task_id not in self.error_callbacks:
            self.error_callbacks[task_id] = []
        self.error_callbacks[task_id].append(callback)

    def get_error_history(self, task_id: str) -> List[Dict[str, Any]]:
        """오류 이력 조회"""
        return self.error_history.get(task_id, [])
