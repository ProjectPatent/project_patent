import asyncio
from typing import Dict, Optional
import time

class RateLimiter:
    """API 호출 속도 제한을 관리하는 클래스"""
    
    def __init__(self, rate_limit: int, per: int):
        """
        rate_limit: 최대 호출 횟수
        per: 호출 가능 시간 (초 단위)
        """
        self.rate_limit = rate_limit
        self.per = per
        self.allowance = rate_limit
        self.last_check = time.monotonic()
    
    def is_allowed(self) -> bool:
        """호출이 허용되는지 확인"""
        current = time.monotonic()
        time_passed = current - self.last_check
        self.last_check = current
        self.allowance += time_passed * (self.rate_limit / self.per)
        
        if self.allowance > self.rate_limit:
            self.allowance = self.rate_limit
        
        if self.allowance < 1.0:
            return False
        else:
            self.allowance -= 1.0
            return True
