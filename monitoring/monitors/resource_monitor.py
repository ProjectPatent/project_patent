# monitors/resource_monitor.py
import asyncio
import psutil
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.base import BaseMonitor
from ..core.metrics import IPRMetrics
from ..core.config import MonitoringConfig
from ..core.exceptions import MonitoringError

logger = logging.getLogger(__name__)

class ResourceMonitorError(MonitoringError):
    """시스템 리소스 모니터링 관련 예외"""
    def __init__(self, message: str, **context):
        super().__init__(message, **context)

class ResourceMonitor(BaseMonitor):
    """시스템 리소스 모니터링"""
    
    def __init__(
        self,
        metrics: IPRMetrics,
        config: MonitoringConfig,
        check_interval: Optional[int] = None
    ):
        super().__init__(metrics, config)
        self.check_interval = check_interval or config.check_interval
        self._last_check: Optional[datetime] = None
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """리소스 모니터링 시작"""
        if self._running:
            raise ResourceMonitorError("Monitor is already running")
        await super().start()
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Resource monitoring started")
        
    async def stop(self):
        """리소스 모니터링 중지"""
        if not self._running:
            raise ResourceMonitorError("Monitor is not running")
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        await super().stop()
        logger.info("Resource monitoring stopped")
        
    async def _monitoring_loop(self):
        """주기적 모니터링 수행"""
        while self._running:
            try:
                health_info = await self.check_health()
                self._update_metrics(health_info)
                self._last_check = datetime.utcnow()
            except Exception as e:
                logger.error(f"Resource monitoring error: {str(e)}", exc_info=True)
                if self.metrics:
                    self.metrics.record_error("monitoring_error", "resource_monitor")
            await asyncio.sleep(self.check_interval)
            
    def _update_metrics(self, health_info: Dict[str, Any]):
        """메트릭 업데이트"""
        if self.metrics:
            self.metrics.memory_usage.set(health_info["memory_used"])
            self.metrics.cpu_percent.set(health_info["cpu_percent"])
            
    async def check_health(self) -> Dict[str, Any]:
        """시스템 리소스 상태 확인"""
        status = await super().get_status()
        status.update({
            "type": "resource_monitor",
            "service": self.config.service_name,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "check_interval": self.check_interval,
            "memory_total": psutil.virtual_memory().total,
            "memory_used": psutil.virtual_memory().used,
            "memory_percent": psutil.virtual_memory().percent,
            "cpu_percent": psutil.cpu_percent(),
            "disk_usage": psutil.disk_usage('/').percent
        })
        return status