"""모니터링 시스템"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import psutil
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    """메트릭 수집기 클래스"""

    def __init__(self):
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def collect_system_metrics(self) -> Dict[str, float]:
        """시스템 메트릭 수집"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent
        }

    async def collect_task_metrics(self, task_id: str) -> Dict[str, Any]:
        """작업별 메트릭 수집"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': await self.collect_system_metrics()
        }

        async with self._lock:
            if task_id not in self.metrics:
                self.metrics[task_id] = []
            self.metrics[task_id].append(metrics)

        return metrics

class ProgressTracker:
    """진행 상황 추적기 클래스"""

    def __init__(self):
        self.progress: Dict[str, float] = {}
        self.start_times: Dict[str, datetime] = {}
        self.end_times: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    async def start_tracking(self, task_id: str) -> None:
        """작업 추적 시작"""
        async with self._lock:
            self.start_times[task_id] = datetime.now()
            self.progress[task_id] = 0.0

    async def update_progress(self, task_id: str, progress: float) -> None:
        """진행 상황 업데이트"""
        async with self._lock:
            self.progress[task_id] = progress

    async def complete_tracking(self, task_id: str) -> None:
        """작업 추적 완료"""
        async with self._lock:
            self.end_times[task_id] = datetime.now()
            self.progress[task_id] = 100.0

    def get_execution_time(self, task_id: str) -> Optional[float]:
        """작업 실행 시간 계산"""
        start_time = self.start_times.get(task_id)
        end_time = self.end_times.get(task_id)

        if start_time and end_time:
            return (end_time - start_time).total_seconds()
        return None

class MonitoringSystem:
    """모니터링 시스템 클래스"""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.progress_tracker = ProgressTracker()
        self.alert_thresholds: Dict[str, float] = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0
        }

    async def start_monitoring(self, task_id: str) -> None:
        """모니터링 시작"""
        await self.progress_tracker.start_tracking(task_id)
        await self.collect_initial_metrics(task_id)

    async def collect_initial_metrics(self, task_id: str) -> None:
        """초기 메트릭 수집"""
        await self.metrics_collector.collect_task_metrics(task_id)

    async def update_progress(self, task_id: str, progress: float) -> None:
        """진행 상황 업데이트 및 메트릭 수집"""
        await self.progress_tracker.update_progress(task_id, progress)
        metrics = await self.metrics_collector.collect_task_metrics(task_id)
        await self.check_thresholds(metrics['system'])

    async def complete_monitoring(self, task_id: str) -> None:
        """모니터링 완료"""
        await self.progress_tracker.complete_tracking(task_id)
        execution_time = self.progress_tracker.get_execution_time(task_id)
        logger.info(f"Task {task_id} completed in {execution_time:.2f} seconds")

    async def check_thresholds(self, metrics: Dict[str, float]) -> None:
        """임계값 확인 및 경고"""
        for metric_name, value in metrics.items():
            threshold = self.alert_thresholds.get(metric_name)
            if threshold and value > threshold:
                logger.warning(
                    f"System metric {metric_name} exceeded threshold: "
                    f"{value:.1f}% > {threshold:.1f}%"
                )
