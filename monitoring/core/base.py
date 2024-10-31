from abc import ABC, abstractmethod
from typing import Dict, Any
from .metrics import IPRMetrics
from .config import MonitoringConfig

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
        
    @abstractmethod
    async def start(self):
        """모니터링 시작"""
        pass
        
    @abstractmethod
    async def stop(self):
        """모니터링 중지"""
        pass
        
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """상태 체크"""
        pass