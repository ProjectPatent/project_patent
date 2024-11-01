# core/metrics.py
from typing import Dict, Any
from prometheus_client import Counter, Summary, Gauge, Histogram
from dataclasses import dataclass
import logging
from .exceptions import MetricError, ValidationError

logger = logging.getLogger(__name__)

@dataclass
class MetricConfig:
    enabled: bool = True
    prefix: str = ""
    labels: tuple = ()
    buckets: tuple = (0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)

class IPRMetrics:
    """통합 IP Rights 메트릭 클래스"""
    def __init__(self, service_name: str, config: MetricConfig = None):
        if not service_name:
            raise ValidationError(
                "Service name cannot be empty",
                field_name="service_name",
                invalid_value=service_name,
                validation_rule="non-empty string required"
            )
        self.service_name = service_name
        self.config = config or MetricConfig()
        self._setup_metrics()
        logger.info(f"Initialized metrics for service: {service_name}")
    
    def _setup_metrics(self):
        try:
            prefix = f"{self.service_name}_"
            
            # API 관련 메트릭
            self.api_requests = Counter(
                f'{prefix}api_requests_total', 
                'Total number of API requests',
                ['endpoint', 'method', 'status']
            )
            
            self.api_latency = Summary(
                f'{prefix}api_latency_seconds',
                'API request latency in seconds',
                ['endpoint', 'method']
            )
            
            self.api_latency_histogram = Histogram(
                f'{prefix}api_latency_histogram_seconds',
                'API request latency distribution',
                ['endpoint', 'method'],
                buckets=self.config.buckets
            )
            
            # 에러 메트릭
            self.errors = Counter(
                f'{prefix}errors_total',
                'Total error count',
                ['type', 'endpoint']
            )

            # 진행 상태 메트릭
            self.processing_progress = Gauge(
                f'{prefix}processing_progress_percent',
                'Current progress of processing'
            )
            
            # 리소스 사용량 메트릭
            self.active_connections = Gauge(
                f'{prefix}active_connections',
                'Number of active connections'
            )
            
            self.memory_usage = Gauge(
                f'{prefix}memory_usage_bytes',
                'Current memory usage'
            )
            
            self.api_total_duration = Gauge(
                f'{prefix}api_total_duration_seconds',
                'Total time from start to finish of API processing'
            )

            # 알림 관련 메트릭
            self.alert_send_time = Summary(
                f'{prefix}alert_send_duration_seconds',
                'Time taken to send alerts',
                ['handler']
            )
            
            self.alert_count = Counter(
                f'{prefix}alerts_total',
                'Total number of alerts',
                ['severity']
            )
            
            self.alert_send_failures = Counter(
                f'{prefix}alert_failures_total',
                'Number of failed alert sends',
                ['handler']
            )
            
            self.alert_history_size = Gauge(
                f'{prefix}alert_history_size',
                'Current size of alert history'
            )
            
            logger.info("Successfully set up all metrics")
            
        except Exception as e:
            logger.error(f"Failed to setup metrics: {str(e)}", exc_info=True)
            raise MetricError(
                "Failed to setup metrics",
                metric_name=f"{prefix}*",
                reason=str(e)
            )

    def increment_requests(self, endpoint: str, method: str, status: str):
        """API 요청 카운터 증가"""
        try:
            self.api_requests.labels(
                endpoint=endpoint,
                method=method,
                status=status
            ).inc()
        except Exception as e:
            logger.error(f"Failed to increment requests counter: {str(e)}")
            raise MetricError(
                "Failed to increment requests counter",
                metric_name="api_requests",
                endpoint=endpoint,
                method=method,
                status=status,
                reason=str(e)
            )

    def record_latency(self, endpoint: str, method: str, duration: float):
        """API 응답 시간 기록"""
        if duration < 0:
            raise MetricError(
                "Latency cannot be negative",
                metric_name="api_latency",
                metric_value=duration,
                endpoint=endpoint,
                method=method
            )
        try:
            # Summary와 Histogram 모두에 기록
            self.api_latency.labels(
                endpoint=endpoint,
                method=method
            ).observe(duration)
            
            self.api_latency_histogram.labels(
                endpoint=endpoint,
                method=method
            ).observe(duration)
            
        except Exception as e:
            logger.error(f"Failed to record latency: {str(e)}")
            raise MetricError(
                "Failed to record latency",
                metric_name="api_latency",
                metric_value=duration,
                endpoint=endpoint,
                method=method,
                reason=str(e)
            )

    def record_error(self, error_type: str, endpoint: str):
        """에러 카운터 증가"""
        try:
            self.errors.labels(
                type=error_type,
                endpoint=endpoint
            ).inc()
            logger.debug(f"Recorded error: type={error_type}, endpoint={endpoint}")
        except Exception as e:
            logger.error(f"Failed to record error: {str(e)}")
            raise MetricError(
                "Failed to record error",
                metric_name="errors",
                error_type=error_type,
                endpoint=endpoint,
                reason=str(e)
            )

    def update_progress(self, progress: float):
        """진행률 업데이트"""
        if not 0 <= progress <= 100:
            raise MetricError(
                "Progress must be between 0 and 100",
                metric_name="processing_progress",
                metric_value=progress,
                validation_rule="0 <= progress <= 100"
            )
        try:
            self.processing_progress.set(progress)
        except Exception as e:
            logger.error(f"Failed to update progress: {str(e)}")
            raise MetricError(
                "Failed to update progress",
                metric_name="processing_progress",
                metric_value=progress,
                reason=str(e)
            )

    def record_alert_send_time(self, handler: str, duration: float):
        """알림 전송 시간 기록"""
        if duration < 0:
            raise MetricError(
                "Alert send time cannot be negative",
                metric_name="alert_send_time",
                metric_value=duration,
                handler=handler
            )
        try:
            self.alert_send_time.labels(handler=handler).observe(duration)
        except Exception as e:
            logger.error(f"Failed to record alert send time: {str(e)}")
            raise MetricError(
                "Failed to record alert send time",
                metric_name="alert_send_time",
                metric_value=duration,
                handler=handler,
                reason=str(e)
            )

    def reset_metrics(self):
        """메트릭 초기화"""
        try:
            for metric in [self.api_requests, self.errors, self.alert_count, self.alert_send_failures]:
                if hasattr(metric, '_metrics'):
                    metric._metrics.clear()
            logger.info("Successfully reset all metrics")
        except Exception as e:
            logger.error(f"Failed to reset metrics: {str(e)}")
            raise MetricError(
                "Failed to reset metrics",
                reason=str(e)
            )

    async def export_metrics(self) -> Dict[str, float]:
        """현재 메트릭 값들을 딕셔너리로 반환"""
        try:
            metrics = {}
            all_metrics = [
                self.api_requests,
                self.api_latency,
                self.errors,
                self.processing_progress,
                self.active_connections,
                self.memory_usage,
                self.api_total_duration,
                self.alert_send_time,
                self.alert_count,
                self.alert_send_failures,
                self.alert_history_size
            ]
            
            for metric in all_metrics:
                for sample in metric.collect()[0].samples:
                    metrics[sample.name] = sample.value
                    
            logger.debug(f"Exported {len(metrics)} metric values")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {str(e)}")
            raise MetricError(
                "Failed to export metrics",
                reason=str(e)
            )