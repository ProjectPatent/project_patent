# prometheus.py
from prometheus_client import start_http_server, REGISTRY
from prometheus_client.core import CollectorRegistry
import logging
import asyncio
from typing import Optional, Dict, Any
from ..core.metrics import IPRMetrics
from ..core.exceptions import MonitoringError

logger = logging.getLogger(__name__)

class PrometheusExporterError(MonitoringError):
    """Prometheus 익스포터 관련 예외"""
    pass

class PrometheusExporter:
    """Prometheus 익스포터"""
    
    def __init__(
        self, 
        metrics: IPRMetrics, 
        port: int = 8000,
        registry: Optional[CollectorRegistry] = None
    ):
        self.metrics = metrics
        self.port = port
        self.registry = registry or REGISTRY
        self._is_running = False
        self._server_task: Optional[asyncio.Task] = None
        logger.info(f"Initialized PrometheusExporter on port {port}")

    async def start(self):
        """Prometheus 메트릭 서버 시작"""
        if self._is_running:
            raise PrometheusExporterError("Exporter is already running")
            
        try:
            # 비동기로 서버 시작
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, start_http_server, self.port)
            self._is_running = True
            
            logger.info(f"PrometheusExporter started on port {self.port}")
            
            # 주기적 메트릭 업데이트 태스크 시작
            self._server_task = asyncio.create_task(self._update_metrics_loop())
            
        except Exception as e:
            logger.error(f"Failed to start PrometheusExporter: {str(e)}", exc_info=True)
            raise PrometheusExporterError(
                "Failed to start Prometheus exporter",
                port=self.port,
                error=str(e)
            ) from e

    async def stop(self):
        """Prometheus 메트릭 서버 중지"""
        if not self._is_running:
            return
            
        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
            
        self._is_running = False
        logger.info("PrometheusExporter stopped")

    async def _update_metrics_loop(self):
        """메트릭 주기적 업데이트"""
        while self._is_running:
            try:
                metrics = await self.metrics.export_metrics()
                self._update_prometheus_metrics(metrics)
            except Exception as e:
                logger.error(f"Failed to update metrics: {str(e)}", exc_info=True)
            await asyncio.sleep(15)  # 15초마다 업데이트

    def _update_prometheus_metrics(self, metrics: Dict[str, Any]):
        """Prometheus 메트릭 업데이트"""
        try:
            for name, value in metrics.items():
                if hasattr(self.metrics, name):
                    metric = getattr(self.metrics, name)
                    if hasattr(metric, 'set'):
                        metric.set(value)
        except Exception as e:
            logger.error(f"Failed to update Prometheus metrics: {str(e)}", exc_info=True)
            raise PrometheusExporterError(
                "Failed to update Prometheus metrics",
                error=str(e)
            ) from e

    @property
    def is_running(self) -> bool:
        """현재 실행 상태 반환"""
        return self._is_running