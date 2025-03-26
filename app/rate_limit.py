"""
Token usage management and Rate Limit handling class.
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
    """Data class for tracking token usage"""
    timestamp: float
    tokens: int


@dataclass
class RetryStats:
    """Data class for tracking retry statistics"""
    last_retry_time: datetime
    retry_count: int
    backoff_factor: float = 1.0
    success_streak: int = 0


@dataclass
class ServerStatus:
    """Data class for tracking server status"""
    last_check: datetime
    is_overloaded: bool = False
    error_count: int = 0
    last_error_time: Optional[datetime] = None


class RateLimitHandler:
    """Class for managing Rate Limits"""

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
            tokens_per_minute (int): Maximum number of tokens allowed per minute
            window_size (int): Time window size in seconds
            max_retries (int): Maximum number of retry attempts
            initial_backoff (float): Initial wait time in seconds
            max_backoff (float): Maximum wait time in seconds
            backoff_multiplier (float): Multiplier for increasing wait time
            max_concurrent (int): Maximum number of concurrent requests
            server_check_interval (int): Server status check interval in seconds
        """
        self.tokens_per_minute = tokens_per_minute
        self.window_size = window_size
        self.usage_history: deque = deque()

        # Retry-related settings
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_multiplier = backoff_multiplier

        # Retry statistics
        self.retry_stats: Dict[str, RetryStats] = {}
        self.usage_patterns: List[TokenUsage] = []
        self.peak_usage_times: List[datetime] = []

        # Concurrency control
        self.concurrent_requests = 0
        self.max_concurrent = max_concurrent
        self._lock = asyncio.Lock()

        # Server status monitoring
        self.server_status = ServerStatus(last_check=datetime.now())
        self.server_check_interval = server_check_interval

    async def check_server_status(self) -> bool:
        """Check the current server status.

        Returns:
            bool: True if server is in normal state
        """
        current_time = datetime.now()

        # Only check if enough time has passed since last check or if server is overloaded
        if (current_time - self.server_status.last_check).seconds >= self.server_check_interval or \
           self.server_status.is_overloaded:

            # Decrease error count (considering recovery over time)
            time_since_error = None
            if self.server_status.last_error_time:
                time_since_error = (current_time - self.server_status.last_error_time).seconds
                if time_since_error > 300:  # If more than 5 minutes have passed
                    self.server_status.error_count = max(0, self.server_status.error_count - 1)

            self.server_status.last_check = current_time

            # Determine server status
            self.server_status.is_overloaded = (
                self.server_status.error_count >= 3 or  # More than 3 errors
                (time_since_error and time_since_error < 60)  # Error within last minute
            )

        return not self.server_status.is_overloaded

    def record_error(self, error_code: int) -> None:
        """Record an error occurrence.

        Args:
            error_code (int): HTTP error code
        """
        if error_code == 529:  # Overload error
            self.server_status.is_overloaded = True
            self.server_status.error_count += 1
            self.server_status.last_error_time = datetime.now()
            logger.warning(f"Server overload detected (Error count: {self.server_status.error_count})")

    async def wait_for_available_slot(self) -> None:
        """Wait for an available request slot."""
        async with self._lock:
            while self.concurrent_requests >= self.max_concurrent:
                logger.warning(f"Concurrent request limit reached. Current: {self.concurrent_requests}/{self.max_concurrent}")
                await asyncio.sleep(1)
            self.concurrent_requests += 1

    async def release_slot(self) -> None:
        """Release a request slot."""
        async with self._lock:
            self.concurrent_requests = max(0, self.concurrent_requests - 1)

    def _cleanup_old_usage(self) -> None:
        """Remove expired usage records."""
        current_time = time.time()
        while self.usage_history and (current_time - self.usage_history[0].timestamp) >= self.window_size:
            self.usage_history.popleft()

    def _update_usage_patterns(self) -> None:
        """Analyze and update usage patterns."""
        current_time = datetime.now()
        current_usage = self.get_current_usage()

        # Update peak usage times
        if current_usage > self.tokens_per_minute * 0.8:  # When usage is above 80%
            self.peak_usage_times.append(current_time)

        # Remove old peak times
        self.peak_usage_times = [
            t for t in self.peak_usage_times
            if current_time - t <= timedelta(hours=24)
        ]

    def _calculate_smart_backoff(self, request_id: str) -> float:
        """Calculate smart backoff duration.

        Args:
            request_id (str): Request identifier

        Returns:
            float: Wait time in seconds
        """
        stats = self.retry_stats.get(request_id)
        if not stats:
            return self.initial_backoff

        # Increase backoff based on server status
        server_multiplier = 2.0 if self.server_status.is_overloaded else 1.0

        # Reduce backoff based on success streak
        backoff_reduction = min(0.5, stats.success_streak * 0.1)

        # Check if current time is during peak hours
        current_time = datetime.now()
        is_peak_time = any(
            current_time - peak_time <= timedelta(minutes=30)
            for peak_time in self.peak_usage_times
        )

        # Calculate base backoff
        backoff = min(
            self.initial_backoff * (self.backoff_multiplier ** stats.retry_count),
            self.max_backoff
        )

        # Increase backoff during peak times
        if is_peak_time:
            backoff *= 1.5

        # Adjust based on server status
        backoff *= server_multiplier

        # Apply success streak reduction
        backoff *= (1 - backoff_reduction)

        return max(self.initial_backoff, backoff)

    async def smart_retry(self, request_id: str, func, *args, **kwargs):
        """Implement smart retry logic.

        Args:
            request_id (str): Request identifier
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Execution result

        Raises:
            Exception: When maximum retry count is exceeded
        """
        if request_id not in self.retry_stats:
            self.retry_stats[request_id] = RetryStats(
                last_retry_time=datetime.now(),
                retry_count=0
            )

        stats = self.retry_stats[request_id]

        while stats.retry_count <= self.max_retries:
            try:
                # Check server status
                if not await self.check_server_status():
                    logger.warning("Server is overloaded, waiting...")
                    await asyncio.sleep(5)
                    continue

                # Concurrency control
                await self.wait_for_available_slot()

                try:
                    result = await func(*args, **kwargs)

                    # Update statistics on success
                    stats.success_streak += 1
                    stats.retry_count = 0
                    stats.backoff_factor = 1.0

                    return result

                finally:
                    # Always release slot
                    await self.release_slot()

            except Exception as e:
                stats.retry_count += 1
                stats.success_streak = 0

                # Check error code and record
                if hasattr(e, 'status_code'):
                    self.record_error(e.status_code)

                if stats.retry_count > self.max_retries:
                    logger.error(f"Maximum retry count ({self.max_retries}) exceeded.")
                    raise e

                backoff_time = self._calculate_smart_backoff(request_id)
                logger.warning(
                    f"Request failed (Attempt {stats.retry_count}/{self.max_retries}). "
                    f"Retrying in {backoff_time:.1f} seconds."
                )

                await asyncio.sleep(backoff_time)
                stats.last_retry_time = datetime.now()

    def get_current_usage(self) -> int:
        """Return total token usage for the current time window."""
        self._cleanup_old_usage()
        return sum(usage.tokens for usage in self.usage_history)

    async def wait_if_needed(self, tokens: int) -> None:
        """Wait if needed to comply with Rate Limit.

        Args:
            tokens (int): Number of tokens to use
        """
        self._update_usage_patterns()
        current_usage = self.get_current_usage()

        if current_usage + tokens > self.tokens_per_minute:
            if self.usage_history:
                oldest_timestamp = self.usage_history[0].timestamp
                current_time = time.time()
                wait_time = max(0, self.window_size - (current_time - oldest_timestamp))

                if wait_time > 0:
                    logger.warning(f"Rate limit reached. Waiting for {wait_time:.1f} seconds.")
                    await asyncio.sleep(wait_time)
                    self._cleanup_old_usage()

    def record_usage(self, tokens: int) -> None:
        """Record token usage."""
        self.usage_history.append(TokenUsage(time.time(), tokens))
        self._cleanup_old_usage()
        self._update_usage_patterns()

    def can_make_request(self, tokens: int) -> bool:
        """Check if a request can be made.

        Args:
            tokens (int): Number of tokens to use

        Returns:
            bool: Whether request can be made
        """
        return (self.get_current_usage() + tokens) <= self.tokens_per_minute

    def get_available_tokens(self) -> int:
        """Return the number of available tokens."""
        return max(0, self.tokens_per_minute - self.get_current_usage())
