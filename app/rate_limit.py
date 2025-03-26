"""
토큰 사용량을 관리하고 Rate Limit을 처리하는 클래스입니다.
"""

import time
import asyncio
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime, timedelta
from app.logger import logger


@dataclass
class TokenUsage:
    """토큰 사용량을 추적하는 데이터 클래스"""
    timestamp: float
    tokens: int


@dataclass
class RetryStats:
    """재시도 통계를 추적하는 데이터 클래스"""
    last_retry_time: datetime
    retry_count: int
    backoff_factor: float = 1.0
    success_streak: int = 0


@dataclass
class ServerStatus:
    """서버 상태를 추적하는 데이터 클래스"""
    last_check: datetime
    is_overloaded: bool = False
    error_count: int = 0
    last_error_time: Optional[datetime] = None


class RateLimitHandler:
    """Rate Limit을 관리하는 클래스"""

    def __init__(
        self,
        tokens_per_minute: int = 40000,
        window_size: int = 60,
        max_retries: int = 5,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        backoff_multiplier: float = 2.0,
        max_concurrent: int = 5,
        server_check_interval: int = 60
    ):
        """
        Args:
            tokens_per_minute (int): 분당 최대 사용 가능한 토큰 수
            window_size (int): 시간 윈도우 크기(초)
            max_retries (int): 최대 재시도 횟수
            initial_backoff (float): 초기 대기 시간(초)
            max_backoff (float): 최대 대기 시간(초)
            backoff_multiplier (float): 대기 시간 증가 배수
            max_concurrent (int): 최대 동시 요청 수
            server_check_interval (int): 서버 상태 체크 주기(초)
        """
        self.tokens_per_minute = tokens_per_minute
        self.window_size = window_size
        self.usage_history: deque = deque()

        # 재시도 관련 설정
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_multiplier = backoff_multiplier

        # 재시도 통계
        self.retry_stats: Dict[str, RetryStats] = {}
        self.usage_patterns: List[TokenUsage] = []
        self.peak_usage_times: List[datetime] = []

        # 동시성 제어
        self.concurrent_requests = 0
        self.max_concurrent = max_concurrent
        self._lock = asyncio.Lock()

        # 서버 상태 모니터링
        self.server_status = ServerStatus(last_check=datetime.now())
        self.server_check_interval = server_check_interval

    async def check_server_status(self) -> bool:
        """서버 상태를 확인합니다.

        Returns:
            bool: 서버가 정상 상태이면 True
        """
        current_time = datetime.now()

        # 마지막 체크로부터 일정 시간이 지났거나 에러가 발생한 경우에만 체크
        if (current_time - self.server_status.last_check).seconds >= self.server_check_interval or \
           self.server_status.is_overloaded:

            # 에러 카운트 감소 (시간 경과에 따른 복구 고려)
            time_since_error = None
            if self.server_status.last_error_time:
                time_since_error = (current_time - self.server_status.last_error_time).seconds
                if time_since_error > 300:  # 5분 이상 지났으면
                    self.server_status.error_count = max(0, self.server_status.error_count - 1)

            self.server_status.last_check = current_time

            # 서버 상태 판단
            self.server_status.is_overloaded = (
                self.server_status.error_count >= 3 or  # 3회 이상 에러
                (time_since_error and time_since_error < 60)  # 1분 이내 에러 발생
            )

        return not self.server_status.is_overloaded

    def record_error(self, error_code: int) -> None:
        """에러를 기록합니다.

        Args:
            error_code (int): HTTP 에러 코드
        """
        if error_code == 529:  # 과부하 에러
            self.server_status.is_overloaded = True
            self.server_status.error_count += 1
            self.server_status.last_error_time = datetime.now()
            logger.warning(f"서버 과부하 감지 (에러 카운트: {self.server_status.error_count})")

    async def wait_for_available_slot(self) -> None:
        """사용 가능한 요청 슬롯을 기다립니다."""
        async with self._lock:
            while self.concurrent_requests >= self.max_concurrent:
                logger.warning(f"동시 요청 제한에 도달. 현재: {self.concurrent_requests}/{self.max_concurrent}")
                await asyncio.sleep(1)
            self.concurrent_requests += 1

    async def release_slot(self) -> None:
        """요청 슬롯을 해제합니다."""
        async with self._lock:
            self.concurrent_requests = max(0, self.concurrent_requests - 1)

    def _cleanup_old_usage(self) -> None:
        """만료된 사용량 기록을 제거합니다."""
        current_time = time.time()
        while self.usage_history and (current_time - self.usage_history[0].timestamp) >= self.window_size:
            self.usage_history.popleft()

    def _update_usage_patterns(self) -> None:
        """사용량 패턴을 분석하고 업데이트합니다."""
        current_time = datetime.now()
        current_usage = self.get_current_usage()

        # 피크 사용량 시간 업데이트
        if current_usage > self.tokens_per_minute * 0.8:  # 80% 이상 사용 시
            self.peak_usage_times.append(current_time)

        # 오래된 피크 시간 제거
        self.peak_usage_times = [
            t for t in self.peak_usage_times
            if current_time - t <= timedelta(hours=24)
        ]

    def _calculate_smart_backoff(self, request_id: str) -> float:
        """스마트 백오프 시간을 계산합니다.

        Args:
            request_id (str): 요청 식별자

        Returns:
            float: 대기해야 할 시간(초)
        """
        stats = self.retry_stats.get(request_id)
        if not stats:
            return self.initial_backoff

        # 서버 상태에 따른 백오프 증가
        server_multiplier = 2.0 if self.server_status.is_overloaded else 1.0

        # 성공 스트릭에 따른 백오프 감소
        backoff_reduction = min(0.5, stats.success_streak * 0.1)

        # 현재 시간이 피크 시간대인지 확인
        current_time = datetime.now()
        is_peak_time = any(
            current_time - peak_time <= timedelta(minutes=30)
            for peak_time in self.peak_usage_times
        )

        # 기본 백오프 계산
        backoff = min(
            self.initial_backoff * (self.backoff_multiplier ** stats.retry_count),
            self.max_backoff
        )

        # 피크 시간대는 백오프 증가
        if is_peak_time:
            backoff *= 1.5

        # 서버 상태에 따른 조정
        backoff *= server_multiplier

        # 성공 스트릭에 따른 감소 적용
        backoff *= (1 - backoff_reduction)

        return max(self.initial_backoff, backoff)

    async def smart_retry(self, request_id: str, func, *args, **kwargs):
        """스마트 재시도 로직을 구현합니다.

        Args:
            request_id (str): 요청 식별자
            func: 실행할 함수
            *args: 함수 인자
            **kwargs: 함수 키워드 인자

        Returns:
            실행 결과

        Raises:
            Exception: 최대 재시도 횟수 초과 시
        """
        if request_id not in self.retry_stats:
            self.retry_stats[request_id] = RetryStats(
                last_retry_time=datetime.now(),
                retry_count=0
            )

        stats = self.retry_stats[request_id]

        while stats.retry_count <= self.max_retries:
            try:
                # 서버 상태 체크
                if not await self.check_server_status():
                    logger.warning("서버 과부하 상태, 잠시 대기...")
                    await asyncio.sleep(5)
                    continue

                # 동시성 제어
                await self.wait_for_available_slot()

                try:
                    result = await func(*args, **kwargs)

                    # 성공 시 통계 업데이트
                    stats.success_streak += 1
                    stats.retry_count = 0
                    stats.backoff_factor = 1.0

                    return result

                finally:
                    # 항상 슬롯 해제
                    await self.release_slot()

            except Exception as e:
                stats.retry_count += 1
                stats.success_streak = 0

                # 에러 코드 확인 및 기록
                if hasattr(e, 'status_code'):
                    self.record_error(e.status_code)

                if stats.retry_count > self.max_retries:
                    logger.error(f"최대 재시도 횟수({self.max_retries})를 초과했습니다.")
                    raise e

                backoff_time = self._calculate_smart_backoff(request_id)
                logger.warning(
                    f"요청 실패 (시도 {stats.retry_count}/{self.max_retries}). "
                    f"{backoff_time:.1f}초 후 재시도합니다."
                )

                await asyncio.sleep(backoff_time)
                stats.last_retry_time = datetime.now()

    def get_current_usage(self) -> int:
        """현재 시간 윈도우의 총 토큰 사용량을 반환합니다."""
        self._cleanup_old_usage()
        return sum(usage.tokens for usage in self.usage_history)

    async def wait_if_needed(self, tokens: int) -> None:
        """필요한 경우 Rate Limit을 준수하기 위해 대기합니다.

        Args:
            tokens (int): 사용하려는 토큰 수
        """
        self._update_usage_patterns()
        current_usage = self.get_current_usage()

        if current_usage + tokens > self.tokens_per_minute:
            if self.usage_history:
                oldest_timestamp = self.usage_history[0].timestamp
                current_time = time.time()
                wait_time = max(0, self.window_size - (current_time - oldest_timestamp))

                if wait_time > 0:
                    logger.warning(f"Rate limit에 도달했습니다. {wait_time:.1f}초 대기합니다.")
                    await asyncio.sleep(wait_time)
                    self._cleanup_old_usage()

    def record_usage(self, tokens: int) -> None:
        """토큰 사용량을 기록합니다."""
        self.usage_history.append(TokenUsage(time.time(), tokens))
        self._cleanup_old_usage()
        self._update_usage_patterns()

    def can_make_request(self, tokens: int) -> bool:
        """요청 가능 여부를 확인합니다.

        Args:
            tokens (int): 사용하려는 토큰 수

        Returns:
            bool: 요청 가능 여부
        """
        return (self.get_current_usage() + tokens) <= self.tokens_per_minute

    def get_available_tokens(self) -> int:
        """현재 사용 가능한 토큰 수를 반환합니다."""
        return max(0, self.tokens_per_minute - self.get_current_usage())
