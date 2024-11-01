# tests/test_metrics.py
import pytest
from monitoring.core.metrics import IPRMetrics, MetricConfig
from monitoring.core.exceptions import MetricError, ValidationError

def test_metrics_initialization(mock_config):
    """메트릭 초기화 테스트"""
    metrics = IPRMetrics(
        service_name=mock_config.service_name,
        config=MetricConfig(enabled=True, prefix="test_")
    )
    assert metrics.service_name == mock_config.service_name
    assert metrics.config.enabled is True

def test_record_latency(mock_metrics):
    """응답 시간 기록 테스트"""
    mock_metrics.record_latency("test_endpoint", "GET", 0.5)
    
    with pytest.raises(MetricError):
        mock_metrics.record_latency("test_endpoint", "GET", -1)

def test_increment_requests(mock_metrics):
    """요청 카운터 증가 테스트"""
    mock_metrics.increment_requests(
        endpoint="test_endpoint",
        method="GET",
        status="success"
    )
    # 카운터가 증가했는지는 메트릭 export로 확인 가능
