# tests/test_monitors.py
import pytest
from unittest.mock import Mock, patch
import asyncio
from monitoring.monitors.api_monitor import APIMonitor, APIMonitorError
from monitoring.monitors.resource_monitor import ResourceMonitor, ResourceMonitorError
from monitoring.core.exceptions import MonitoringError

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
    assert "running" in health_info
    assert "start_time" in health_info
    assert "uptime_seconds" in health_info
    
    # 중지
    await monitor.stop()
    assert monitor._running is False
    assert monitor._monitor_task is None

@pytest.mark.asyncio
async def test_api_monitor_metrics_update(mock_metrics, mock_config):
    """API 모니터 메트릭 업데이트 테스트"""
    monitor = APIMonitor(metrics=mock_metrics, config=mock_config)
    
    # 메트릭 업데이트 모니터링
    await monitor.start()
    await asyncio.sleep(0.1)  # 메트릭 업데이트 대기
    
    # 메트릭 업데이트 확인
    health_info = await monitor.check_health()
    monitor.metrics.active_connections.set.assert_called()  # mock 메트릭 확인
    
    await monitor.stop()

@pytest.mark.asyncio
async def test_resource_monitor_lifecycle(mock_metrics, mock_config):
    """리소스 모니터 라이프사이클 테스트"""
    monitor = ResourceMonitor(metrics=mock_metrics, config=mock_config)
    
    # 초기 상태 확인
    assert not monitor._running
    assert monitor._monitor_task is None
    
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
    assert "memory_used" in health_info
    assert "cpu_percent" in health_info
    assert "disk_percent" in health_info
    
    # 중지
    await monitor.stop()
    assert monitor._running is False
    assert monitor._monitor_task is None

@pytest.mark.asyncio
async def test_resource_monitor_metrics(mock_metrics, mock_config):
    """리소스 모니터 메트릭 수집 테스트"""
    with patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.cpu_percent') as mock_cpu, \
         patch('psutil.disk_usage') as mock_disk:
        
        # Mock psutil 반환값 설정
        mock_memory.return_value = Mock(
            total=100000,
            used=50000,
            percent=50.0
        )
        mock_cpu.return_value = 30.0
        mock_disk.return_value = Mock(
            total=1000000,
            used=300000,
            percent=30.0
        )
        
        monitor = ResourceMonitor(metrics=mock_metrics, config=mock_config)
        await monitor.start()
        
        # 메트릭 수집 확인
        health_info = await monitor.check_health()
        assert health_info['memory_percent'] == 50.0
        assert health_info['cpu_percent'] == 30.0
        assert health_info['disk_percent'] == 30.0
        
        # 메트릭 업데이트 확인
        monitor.metrics.memory_usage.set.assert_called()  # mock 메트릭 확인
        
        await monitor.stop()

@pytest.mark.asyncio
async def test_monitor_error_handling(mock_metrics, mock_config):
    """모니터 에러 처리 테스트"""
    mock_config.check_interval = 0.1  # 빠른 테스트를 위한 설정
    
    class ErrorMonitor(APIMonitor):
        async def check_health(self):
            raise Exception("Simulated error")
    
    monitor = ErrorMonitor(metrics=mock_metrics, config=mock_config)
    
    await monitor.start()
    await asyncio.sleep(0.2)  # 에러 발생 대기
    
    # 에러가 발생해도 모니터링은 계속 실행
    assert monitor._running is True
    assert monitor.metrics.errors.labels.call_count > 0  # 에러 메트릭 기록 확인
    
    await monitor.stop()