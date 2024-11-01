# base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from .metrics import IPRMetrics
from .config import MonitoringConfig
from .exceptions import MonitoringError

logger = logging.getLogger(__name__)

class BaseMonitor(ABC):
    """모니터링 기본 클래스"""
    
    def __init__(
        self,
        metrics: IPRMetrics,
        config: MonitoringConfig
    ):
        self.metrics = metrics
        self.config = config
        self._running = False
        self._start_time: Optional[datetime] = None
        logger.info(f"Initializing {self.__class__.__name__}")
        
    @abstractmethod
    async def start(self):
        """모니터링 시작"""
        if self._running:
            raise MonitoringError("Monitor is already running")
        self._running = True
        self._start_time = datetime.utcnow()
        logger.info(f"{self.__class__.__name__} started")
        
    @abstractmethod
    async def stop(self):
        """모니터링 중지"""
        if not self._running:
            raise MonitoringError("Monitor is not running")
        self._running = False
        logger.info(f"{self.__class__.__name__} stopped")
        
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """상태 체크"""
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """모니터 상태 정보 반환"""
        return {
            "running": self._running,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "uptime_seconds": (datetime.utcnow() - self._start_time).total_seconds() 
                            if self._start_time else 0
        }