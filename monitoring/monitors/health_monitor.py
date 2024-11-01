# monitors/health_monitor.py
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.base import BaseMonitor
from ..core.metrics import IPRMetrics
from ..core.config import MonitoringConfig

logger = logging.getLogger(__name__)

class HealthMonitor(BaseMonitor):
    """전체 시스템 헬스 체크"""
    
    def __init__(
        self,
        metrics: IPRMetrics,
        config: MonitoringConfig,
        monitors: List[BaseMonitor]
    ):
        super().__init__(metrics, config)
        self.monitors = monitors
        self._last_health_check: Optional[datetime] = None
        
    async def start(self):
        """헬스 모니터링 시작"""
        await super().start()
        # 다른 모니터들도 시작
        for monitor in self.monitors:
            await monitor.start()
        logger.info("Health monitoring started")
        
    async def stop(self):
        """헬스 모니터링 중지"""
        # 다른 모니터들도 중지
        for monitor in self.monitors:
            await monitor.stop()
        await super().stop()
        logger.info("Health monitoring stopped")
        
    async def check_health(self) -> Dict[str, Any]:
        """전체 시스템 상태 확인"""
        health_status = await super().get_status()
        
        # 각 모니터의 상태 수집
        monitors_status = {}
        for monitor in self.monitors:
            try:
                monitor_health = await monitor.check_health()
                monitors_status[monitor.__class__.__name__] = {
                    "status": "healthy",
                    "details": monitor_health
                }
            except Exception as e:
                logger.error(f"Health check failed for {monitor.__class__.__name__}: {str(e)}")
                monitors_status[monitor.__class__.__name__] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                
        health_status.update({
            "last_check": self._last_health_check.isoformat() if self._last_health_check else None,
            "monitors": monitors_status
        })
        
        self._last_health_check = datetime.utcnow()
        return health_status