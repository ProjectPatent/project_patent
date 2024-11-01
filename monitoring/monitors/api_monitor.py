# monitors/api_monitor.py
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.base import BaseMonitor
from ..core.metrics import IPRMetrics
from ..core.config import MonitoringConfig
from ..core.exceptions import MonitoringError

logger = logging.getLogger(__name__)

class APIMonitor(BaseMonitor):
    """API 호출 모니터링"""
    
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
        """API 모니터링 시작"""
        await super().start()
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("API monitoring started")
        
    async def stop(self):
        """API 모니터링 중지"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        await super().stop()
        logger.info("API monitoring stopped")
        
    async def _monitoring_loop(self):
        """주기적 모니터링 수행"""
        while self._running:
            try:
                health_info = await self.check_health()
                self._update_metrics(health_info)
                self._last_check = datetime.utcnow()
            except Exception as e:
                logger.error(f"API monitoring error: {str(e)}", exc_info=True)
                self.metrics.record_error("monitoring_error", "api_monitor")
            await asyncio.sleep(self.check_interval)
            
    def _update_metrics(self, health_info: Dict[str, Any]):
        """메트릭 업데이트"""
        # 상태 정보를 기반으로 메트릭 업데이트
        self.metrics.active_connections.set(health_info.get("active_connections", 0))
        self.metrics.api_total_duration.set(health_info.get("total_duration", 0))
        
    async def check_health(self) -> Dict[str, Any]:
        """API 상태 확인"""
        status = await super().get_status()
        status.update({
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "check_interval": self.check_interval
        })
        return status