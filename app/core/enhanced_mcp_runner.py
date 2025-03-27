"""향상된 MCP 실행기"""

import asyncio
from typing import Dict, Any, Optional, List
import logging

from .task_management.manager import TaskManager
from .state_management.state_manager import StateManager
from .error_handling.error_handler import ErrorHandler
from .monitoring.monitor import MonitoringSystem

logger = logging.getLogger(__name__)

class EnhancedMCPRunner:
    """향상된 MCP 실행기 클래스"""

    def __init__(self):
        self.task_manager = TaskManager()
        self.state_manager = StateManager()
        self.error_handler = ErrorHandler()
        self.monitoring = MonitoringSystem()

    async def process_complex_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """복잡한 요청 처리"""
        try:
            # 1. 작업 생성
            task = await self.task_manager.create_task(
                description=request.get('description', 'Complex request processing')
            )

            # 2. 모니터링 시작
            await self.monitoring.start_monitoring(task.id)

            # 3. 작업 분할
            subtasks = await self.decompose_request(request, task.id)

            # 4. 작업 실행
            results = await self.execute_subtasks(subtasks)

            # 5. 결과 취합
            final_result = await self.combine_results(results)

            # 6. 모니터링 완료
            await self.monitoring.complete_monitoring(task.id)

            return {
                'task_id': task.id,
                'status': 'completed',
                'result': final_result
            }

        except Exception as e:
            logger.error(f"Failed to process request: {str(e)}", exc_info=True)
            return {
                'status': 'failed',
                'error': str(e)
            }

    async def decompose_request(self, request: Dict[str, Any], parent_task_id: str) -> List[Dict[str, Any]]:
        """요청을 하위 작업으로 분할"""
        try:
            # 1. 상태 초기화
            await self.state_manager.set_state(parent_task_id, {
                'status': 'decomposing',
                'request': request
            })

            # 2. 작업 분할
            subtasks = []
            for i, part in enumerate(self._split_request(request)):
                subtask = await self.task_manager.create_task(
                    description=f"Subtask {i+1} of {parent_task_id}",
                    dependencies=[{'task_id': parent_task_id, 'type': 'parent'}]
                )
                subtasks.append({
                    'task': subtask,
                    'data': part
                })

            # 3. 상태 업데이트
            await self.state_manager.update_state(parent_task_id, {
                'status': 'decomposed',
                'subtask_count': len(subtasks)
            })

            return subtasks

        except Exception as e:
            await self.error_handler.handle_error(parent_task_id, e)
            raise

    async def execute_subtasks(self, subtasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """하위 작업 실행"""
        results = []
        total_tasks = len(subtasks)

        for i, subtask_info in enumerate(subtasks):
            subtask = subtask_info['task']
            try:
                # 1. 작업 실행 준비
                await self.state_manager.set_state(subtask.id, {
                    'status': 'executing',
                    'data': subtask_info['data']
                })

                # 2. 작업 실행
                result = await self._execute_single_task(subtask, subtask_info['data'])

                # 3. 결과 저장
                results.append({
                    'task_id': subtask.id,
                    'result': result
                })

                # 4. 진행 상황 업데이트
                progress = ((i + 1) / total_tasks) * 100
                await self.monitoring.update_progress(subtask.id, progress)

            except Exception as e:
                if await self.error_handler.handle_error(subtask.id, e):
                    # 재시도 가능한 경우
                    i -= 1  # 현재 작업 재시도
                    continue
                else:
                    # 재시도 불가능한 경우
                    raise

        return results

    async def _execute_single_task(self, task: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """단일 작업 실행"""
        try:
            # 1. 체크포인트 저장
            await self.state_manager.save_checkpoint(task.id, {
                'status': 'executing',
                'data': data
            })

            # 2. 작업 실행
            # 실제 작업 실행 로직은 구체적인 요구사항에 따라 구현
            result = await self._process_task_data(data)

            # 3. 상태 업데이트
            await self.state_manager.update_state(task.id, {
                'status': 'completed',
                'result': result
            })

            return result

        except Exception as e:
            # 4. 오류 발생 시 체크포인트에서 복구 시도
            checkpoint = await self.state_manager.restore_from_checkpoint(task.id)
            if checkpoint:
                return await self._execute_single_task(task, checkpoint['data'])
            raise

    async def combine_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """작업 결과 취합"""
        # 결과 취합 로직은 구체적인 요구사항에 따라 구현
        combined = {
            'results': results,
            'summary': {
                'total_tasks': len(results),
                'successful_tasks': sum(1 for r in results if 'error' not in r),
                'failed_tasks': sum(1 for r in results if 'error' in r)
            }
        }
        return combined

    def _split_request(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """요청을 하위 작업으로 분할하는 로직"""
        # 실제 분할 로직은 구체적인 요구사항에 따라 구현
        # 예시로 단순히 리스트로 반환
        return [request]

    async def _process_task_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """작업 데이터 처리 로직"""
        # 실제 처리 로직은 구체적인 요구사항에 따라 구현
        return {'processed': data}
