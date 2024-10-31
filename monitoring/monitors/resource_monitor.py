from typing import Dict, Any
from monitoring.core.metrics import IPRMetrics
from monitoring.core.config import MonitoringConfig
from monitoring.core.base import BaseMonitor
import psutil

class ResourceMonitor(BaseMonitor):
    """시스템 리소스 모니터링 클래스"""

    def __init__(self, metrics: IPRMetrics, config: MonitoringConfig):
        super().__init__(metrics, config)
    
    async def start(self):
        self._running = True
        # 리소스 모니터링을 시작하는 로직을 추가할 수 있습니다.
    
    async def stop(self):
        self._running = False
        # 리소스 모니터링을 중지하는 로직을 추가할 수 있습니다.

    async def check_health(self) -> Dict[str, Any]:
        # 현재 메모리와 CPU 사용량을 수집하여 반환합니다.
        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent(interval=1)
        return {"memory_usage": memory_usage, "cpu_usage": cpu_usage}
