# monitors/health_monitor.py
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..core.base import BaseMonitor
from ..core.metrics import IPRMetrics
from ..core.config import MonitoringConfig
from ..core.exceptions import MonitoringError

logger = logging.getLogger(__name__)

class HealthMonitorError(MonitoringError):
    """헬스체크 모니터링 관련 예외"""
    def __init__(self, message: str, **context):
        super().__init__(message, **context)

class HealthMonitor(BaseMonitor):
    """시스템 전반의 헬스체크 모니터링"""
    
    def __init__(
        self,
        metrics: IPRMetrics,
        config: MonitoringConfig,
        monitors: Optional[List[BaseMonitor]] = None,
        check_interval: Optional[int] = None
    ):
        super().__init__(metrics, config)
        self.monitors = monitors or []
        self.check_interval = check_interval or config.check_interval
        self._last_check: Optional[datetime] = None
        self._monitor_task: Optional[asyncio.Task] = None

    async def start(self):
        if self._running:
            raise HealthMonitorError("Monitor is already running")
        await super().start()
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")

    async def stop(self):
        if not self._running:
            raise HealthMonitorError("Monitor is not running")
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        await super().stop()
        logger.info("Health monitoring stopped")

    async def _monitoring_loop(self):
        while self._running:
            try:
                health_info = await self.check_health()
                self._last_check = datetime.utcnow()
            except Exception as e:
                logger.error(f"Health monitoring error: {str(e)}", exc_info=True)
                if self.metrics:
                    self.metrics.record_error("monitoring_error", "health_monitor")
            await asyncio.sleep(self.check_interval)

    async def check_health(self) -> Dict[str, Any]:
        status = await super().get_status()
        monitors_health = {}

        for monitor in self.monitors:
            try:
                monitors_health[monitor.__class__.__name__] = await monitor.check_health()
            except Exception as e:
                logger.error(f"Monitor check failed: {str(e)}", exc_info=True)
                monitors_health[monitor.__class__.__name__] = {"error": str(e)}

        status.update({
            "type": "health_monitor",
            "service": self.config.service_name,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "check_interval": self.check_interval,
            "monitors": monitors_health
        })
        return status