import asyncio
import psutil
from ..core.metrics import IPRMetrics

class ResourceMonitor:
    def __init__(self, metrics: IPRMetrics):
        self.metrics = metrics
        self._monitoring = False

    async def start(self):
        self._monitoring = True
        while self._monitoring:
            try:
                # 리소스 사용량 체크
                self._check_resource_usage()
            except Exception as e:
                self.metrics.errors.labels(
                    type='monitoring_error',
                    endpoint='resource_monitor'
                ).inc()
            await asyncio.sleep(60)  # 1분마다 체크

    async def stop(self):
        self._monitoring = False

    def _check_resource_usage(self):
        """CPU 및 메모리 사용량을 수집하고 메트릭을 업데이트"""
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        self.metrics.active_connections.set(cpu_usage)
        self.metrics.memory_usage.set(memory_usage)
