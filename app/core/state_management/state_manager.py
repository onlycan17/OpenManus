"""상태 관리 시스템"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import json

class StateManager:
    """상태 관리자 클래스"""

    def __init__(self):
        self.states: Dict[str, Dict[str, Any]] = {}
        self.checkpoints: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def set_state(self, task_id: str, state: Dict[str, Any]) -> None:
        """작업 상태 설정"""
        async with self._lock:
            self.states[task_id] = {
                **state,
                'updated_at': datetime.now().isoformat()
            }

    async def get_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        return self.states.get(task_id)

    async def save_checkpoint(self, task_id: str, state: Dict[str, Any]) -> None:
        """체크포인트 저장"""
        checkpoint = {
            'state': state,
            'timestamp': datetime.now().isoformat()
        }
        async with self._lock:
            self.checkpoints[task_id] = checkpoint

    async def restore_from_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """체크포인트에서 상태 복원"""
        if checkpoint := self.checkpoints.get(task_id):
            return checkpoint['state']
        return None

    async def update_state(self, task_id: str, updates: Dict[str, Any]) -> None:
        """작업 상태 부분 업데이트"""
        async with self._lock:
            if current_state := self.states.get(task_id):
                self.states[task_id] = {
                    **current_state,
                    **updates,
                    'updated_at': datetime.now().isoformat()
                }

    async def clear_state(self, task_id: str) -> None:
        """작업 상태 제거"""
        async with self._lock:
            self.states.pop(task_id, None)
            self.checkpoints.pop(task_id, None)

    def serialize_state(self, state: Dict[str, Any]) -> str:
        """상태 정보 직렬화"""
        return json.dumps(state, default=str)

    def deserialize_state(self, state_str: str) -> Dict[str, Any]:
        """상태 정보 역직렬화"""
        return json.loads(state_str)
