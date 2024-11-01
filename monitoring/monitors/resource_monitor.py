# monitors/resource_monitor.py
import psutil
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.base import BaseMonitor
from ..core.metrics import IPRMetrics
from ..core.config import MonitoringConfig

logger = logging.getLogger(__name__)

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
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """리소스 모니터링 시작"""
        await super().start()
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Resource monitoring started")
        
    async def stop(self):
        """리소스 모니터링 중지"""
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
        """주기적 리소스 모니터링"""
        while self._running:
            try:
                health_info = await self.check_health()
                self._update_metrics(health_info)
            except Exception as e:
                logger.error(f"Resource monitoring error: {str(e)}", exc_info=True)
                self.metrics.record_error("monitoring_error", "resource_monitor")
            await asyncio.sleep(self.check_interval)
            
    def _update_metrics(self, health_info: Dict[str, Any]):
        """메트릭 업데이트"""
        self.metrics.memory_usage.set(health_info["memory_used"])
        
    async def check_health(self) -> Dict[str, Any]:
        """리소스 상태 확인"""
        status = await super().get_status()
        
        # 시스템 리소스 정보 수집
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        
        status.update({
            "memory_total": memory.total,
            "memory_used": memory.used,
            "memory_percent": memory.percent,
            "cpu_percent": cpu_percent,
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_percent": disk.percent
        })
        return status