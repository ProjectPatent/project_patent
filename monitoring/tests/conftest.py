# tests/conftest.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from monitoring.core.config import MonitoringConfig
from monitoring.core.metrics import IPRMetrics, MetricConfig
from monitoring.alerts.manager import AlertManager, Alert, AlertSeverity

@pytest.fixture
def mock_config():
    """테스트용 설정 객체"""
    config = MonitoringConfig(
        service_name="test_service",
        enabled=True,
        prometheus_port=8001,
        check_interval=1,
        log_level="INFO"
    )
    return config

@pytest.fixture
def mock_metrics(mock_config):
    """테스트용 메트릭 객체"""
    return IPRMetrics(
        service_name=mock_config.service_name,
        config=MetricConfig(enabled=True, prefix="test_")
    )

@pytest.fixture
async def alert_manager():
    """테스트용 알림 매니저"""
    manager = AlertManager(max_history=10)
    yield manager
    await manager.clear_history()

@pytest.fixture
def mock_alert():
    """테스트용 알림 객체"""
    return Alert(
        title="Test Alert",
        message="Test Message",
        severity=AlertSeverity.WARNING,
        timestamp=datetime.utcnow(),
        metadata={"test_key": "test_value"}
    )

@pytest.fixture
def mock_prometheus_registry():
    """테스트용 Prometheus 레지스트리"""
    with patch('prometheus_client.CollectorRegistry') as mock_registry:
        yield mock_registry()