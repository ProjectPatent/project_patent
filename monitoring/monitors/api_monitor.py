# monitors/api_monitor.py
import asyncio
from ..core.metrics import IPRMetrics

class APIMonitor:
    def __init__(self, metrics: IPRMetrics):
        self.metrics = metrics
        self._monitoring = False
        
    async def start(self):
        self._monitoring = True
        while self._monitoring:
            try:
                # API 상태 체크
                await self._check_api_status()
            except Exception as e:
                self.metrics.errors.labels(
                    type='monitoring_error',
                    endpoint='api_monitor'
                ).inc()
            await asyncio.sleep(60)  # 1분마다 체크
            
    async def stop(self):
        self._monitoring = False