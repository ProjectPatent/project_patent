from prometheus_client import start_http_server
from ..core.metrics import IPRMetrics
import logging

class PrometheusExporter:
    """Prometheus 익스포터 클래스: Prometheus 서버와 메트릭 통합"""

    def __init__(self, metrics: IPRMetrics, port: int = 8000):
        self.metrics = metrics
        self.port = port
        self._is_running = False

    def start(self):
        """Prometheus 메트릭 서버 시작"""
        if not self._is_running:
            try:
                start_http_server(self.port)
                self._is_running = True
                logging.info(f"PrometheusExporter started on port {self.port}")
            except Exception as e:
                logging.error(f"Failed to start PrometheusExporter: {str(e)}")
                raise

    def stop(self):
        """Prometheus 메트릭 서버 중지"""
        # Prometheus client는 기본적으로 서버 중지를 직접 제공하지 않음
        # 이 부분은 애플리케이션 전체를 중지할 때 종료되는 형태로 구성 필요
        self._is_running = False
        logging.info("PrometheusExporter stopped (process will exit to stop server)")

    def export_metrics(self):
        """Prometheus와 호환되는 메트릭 내보내기 (테스트용)"""
        try:
            return self.metrics.export_metrics()
        except Exception as e:
            logging.error(f"Failed to export metrics: {str(e)}")
            raise
