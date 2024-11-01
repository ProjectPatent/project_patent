# rate_limiter.py
import asyncio
from collections import deque
import time
import logging
from typing import Optional
from ..core.exceptions import MonitoringError

logger = logging.getLogger(__name__)

class RateLimitError(MonitoringError):
    """속도 제한 관련 예외"""
    pass

class RateLimiter:
    """API 호출 속도 제한 관리"""
    
    def __init__(self, max_requests: int = 50, window_size: float = 1.0):
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = deque()
        self._lock = asyncio.Lock()

    async def wait_if_needed(self):
        """요청 속도 제한을 위한 대기 로직"""
        async with self._lock:
            now = time.time()
            # 윈도우 밖의 요청 제거
            while self.requests and now - self.requests[0] > self.window_size:
                self.requests.popleft()
                
            if len(self.requests) >= self.max_requests:
                sleep_time = self.requests[0] + self.window_size - now
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached, waiting for {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
                    
            self.requests.append(now)
            logger.debug(f"Current request count: {len(self.requests)}")

    async def acquire(self):
        """요청 권한 획득"""
        try:
            await self.wait_if_needed()
        except Exception as e:
            logger.error(f"Failed to acquire rate limit: {str(e)}", exc_info=True)
            raise RateLimitError("Failed to acquire rate limit") from e