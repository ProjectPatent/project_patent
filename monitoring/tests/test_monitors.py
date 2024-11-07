# tests/test_monitors.py
import pytest
from unittest.mock import Mock, patch
import asyncio
from monitoring.monitors.api_monitor import APIMonitor, APIMonitorError
from monitoring.monitors.resource_monitor import ResourceMonitor, ResourceMonitorError
from monitoring.core.config import MonitoringConfig
from monitoring.core.metrics import IPRMetrics

@pytest.fixture
def mock_metrics():
    """Mock metrics with necessary attributes."""
    metrics = Mock(spec=IPRMetrics)
    
    # Mock individual metric methods and attributes
    metrics.active_connections = Mock()
    metrics.active_connections.set = Mock()
    
    metrics.memory_usage = Mock()
    metrics.memory_usage.set = Mock()
    
    metrics.api_total_duration = Mock()
    metrics.api_total_duration.set = Mock()
    
    metrics.errors = Mock()
    metrics.errors.labels = Mock(return_value=Mock(inc=Mock()))
    
    # Add other necessary mocked metrics if needed
    return metrics

@pytest.fixture
def mock_config():
    """Mock configuration object."""
    config = Mock(spec=MonitoringConfig)
    
    # Mock get_value method
    def get_value_side_effect(key, default=None):
        config_values = {
            "slack_webhook_url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
            "slack_timeout": 10,
            "check_interval": 60
        }
        return config_values.get(key, default)
    
    config.get_value.side_effect = get_value_side_effect
    
    # Mock get_section method
    def get_section_side_effect(section):
        sections = {
            "smtp": {
                "host": "smtp.example.com",
                "port": 587,
                "from_address": "no-reply@example.com",
                "to_address": "user@example.com",
                "use_tls": True,
                "username": "smtp_user",
                "password": "smtp_pass"
            }
        }
        return sections.get(section, {})
    
    config.get_section.side_effect = get_section_side_effect
    
    # 필요한 속성 추가
    config.service_name = "TestService"  # 서비스 이름 추가
    config.check_interval = 60
    config.some_other_attribute = "value"  # 필요한 다른 속성들도 추가
    
    return config

@pytest.mark.asyncio
async def test_api_monitor_lifecycle(mock_metrics, mock_config):
    """API 모니터 라이프사이클 테스트"""
    monitor = APIMonitor(metrics=mock_metrics, config=mock_config)
    
    # 초기 상태 확인
    assert not monitor._running
    assert monitor._monitor_task is None
    
    # 시작
    await monitor.start()
    assert monitor._running is True
    assert monitor._monitor_task is not None
    assert isinstance(monitor._monitor_task, asyncio.Task)
    
    # 중복 시작 시도
    with pytest.raises(APIMonitorError):
        await monitor.start()
    
    # 상태 확인
    health_info = await monitor.check_health()
    assert isinstance(health_info, dict)
    assert "type" in health_info
    assert health_info["type"] == "api_monitor"
    assert "service" in health_info
    assert health_info["service"] == "TestService"
    assert "last_check" in health_info
    assert "check_interval" in health_info
    assert "active_connections" in health_info
    assert "api_total_duration_seconds" in health_info
    
    # 중지
    await monitor.stop()
    assert monitor._running is False
    assert monitor._monitor_task is None

@pytest.mark.asyncio
async def test_api_monitor_metrics_update(mock_metrics, mock_config):
    """API 모니터 메트릭 업데이트 테스트"""
    monitor = APIMonitor(metrics=mock_metrics, config=mock_config)
    
    # psutil 함수들을 패치합니다.
    with patch('monitoring.monitors.api_monitor.psutil.virtual_memory') as mock_virtual_memory, \
         patch('monitoring.monitors.api_monitor.psutil.cpu_percent') as mock_cpu_percent, \
         patch('monitoring.monitors.api_monitor.psutil.disk_usage') as mock_disk_usage, \
         patch('monitoring.monitors.api_monitor.psutil.net_connections', return_value=[]):
        
        # Mock psutil 반환값 설정
        mock_virtual_memory.return_value = Mock(
            total=100000,
            used=50000,
            percent=50.0
        )
        mock_cpu_percent.return_value = 30.0
        mock_disk_usage.return_value = Mock(
            total=1000000,
            used=300000,
            percent=30.0
        )
    
        # 메트릭 업데이트를 트리거하기 위해 모니터 시작
        await monitor.start()
        health_info = await monitor.check_health()
        
        # 메트릭 업데이트 확인
        mock_metrics.active_connections.set.assert_called_with(health_info.get("active_connections", 0))
        mock_metrics.api_total_duration.set.assert_called_with(health_info.get("api_total_duration_seconds", 0))
        
        await monitor.stop()

@pytest.mark.asyncio
async def test_resource_monitor_lifecycle(mock_metrics, mock_config):
    """리소스 모니터 라이프사이클 테스트"""
    monitor = ResourceMonitor(metrics=mock_metrics, config=mock_config)
    
    # 초기 상태 확인
    assert not monitor._running
    assert monitor._monitor_task is None
    
    # psutil 함수들을 패치합니다.
    with patch('monitoring.monitors.resource_monitor.psutil.virtual_memory') as mock_virtual_memory, \
         patch('monitoring.monitors.resource_monitor.psutil.cpu_percent') as mock_cpu_percent, \
         patch('monitoring.monitors.resource_monitor.psutil.disk_usage') as mock_disk_usage, \
         patch('monitoring.monitors.resource_monitor.psutil.net_connections', return_value=[]):
        
        # Mock psutil 반환값 설정
        mock_virtual_memory.return_value = Mock(
            total=100000,
            used=50000,
            percent=50.0
        )
        mock_cpu_percent.return_value = 30.0
        mock_disk_usage.return_value = Mock(
            total=1000000,
            used=300000,
            percent=30.0
        )
        
        # 시작
        await monitor.start()
        assert monitor._running is True
        assert monitor._monitor_task is not None
        
        # 중복 시작 시도
        with pytest.raises(ResourceMonitorError):
            await monitor.start()
        
        # 상태 확인
        health_info = await monitor.check_health()
        assert isinstance(health_info, dict)
        assert "memory_usage_bytes" in health_info
        assert "active_connections" in health_info
        assert health_info["memory_usage_bytes"] == 50000
        assert health_info["active_connections"] == 0
        
        # 메트릭 업데이트 확인
        mock_metrics.memory_usage.set.assert_called_with(50000)
        mock_metrics.active_connections.set.assert_called_with(0)
        
        # 중지
        await monitor.stop()
        assert monitor._running is False
        assert monitor._monitor_task is None

@pytest.mark.asyncio
async def test_resource_monitor_metrics(mock_metrics, mock_config):
    """리소스 모니터 메트릭 수집 테스트"""
    with patch('monitoring.monitors.resource_monitor.psutil.virtual_memory') as mock_virtual_memory, \
         patch('monitoring.monitors.resource_monitor.psutil.cpu_percent') as mock_cpu_percent, \
         patch('monitoring.monitors.resource_monitor.psutil.disk_usage') as mock_disk_usage, \
         patch('monitoring.monitors.resource_monitor.psutil.net_connections', return_value=[]):
        
        # Mock psutil 반환값 설정
        mock_virtual_memory.return_value = Mock(
            total=100000,
            used=50000,
            percent=50.0
        )
        mock_cpu_percent.return_value = 30.0
        mock_disk_usage.return_value = Mock(
            total=1000000,
            used=300000,
            percent=30.0
        )
        
        monitor = ResourceMonitor(metrics=mock_metrics, config=mock_config)
        await monitor.start()
        
        # 메트릭 수집 확인
        health_info = await monitor.check_health()
        assert health_info['memory_usage_bytes'] == 50000
        assert health_info['cpu_percent'] == 30.0
        assert health_info['disk_percent'] == 30.0
        
        # 메트릭 업데이트 확인
        mock_metrics.memory_usage.set.assert_called_with(50000)
        mock_metrics.active_connections.set.assert_called_with(0)  # net_connections이 빈 리스트를 반환하므로
        
        await monitor.stop()

@pytest.mark.asyncio
async def test_monitor_error_handling(mock_metrics, mock_config):
    """모니터 에러 처리 테스트"""
    
    class ErrorMonitor(APIMonitor):
        async def check_health(self):
            raise Exception("Simulated error")
    
    monitor = ErrorMonitor(metrics=mock_metrics, config=mock_config)
    
    with patch('monitoring.monitors.api_monitor.psutil.net_connections', return_value=[]):
        await monitor.start()
        await asyncio.sleep(0.2)  # 에러 발생 대기
        
        # 에러가 발생해도 모니터링은 계속 실행
        assert monitor._running is True
        mock_metrics.errors.labels.assert_called_with(type='api_monitor', endpoint='api')
        mock_metrics.errors.labels().inc.assert_called()
        
        await monitor.stop()