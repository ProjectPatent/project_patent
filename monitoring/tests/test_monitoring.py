# tests/test_monitoring.py
import pytest
import asyncio
from monitoring.core.config import MonitoringConfig
from monitoring.core.metrics import IPRMetrics
from monitoring.monitors.api_monitor import APIMonitor
from monitoring.monitors.resource_monitor import ResourceMonitor

@pytest.mark.asyncio
async def test_system():
    # 1. 기본 설정으로 시작
    config = MonitoringConfig(
        service_name="test_monitor",
        check_interval=0.1  # 빠른 체크 간격 설정
    )
    metrics = IPRMetrics("test_monitor")
    
    # 2. API 모니터 테스트
    api_monitor = APIMonitor(metrics=metrics, config=config)
    print("API 모니터 시작 전:", api_monitor._running)  # False여야 함
    
    await api_monitor.start()
    print("API 모니터 시작 후:", api_monitor._running)  # True여야 함
    
    # 3. 상태 확인
    health = await api_monitor.check_health()
    print("API 상태:", health)
    
    # 4. 리소스 모니터 테스트
    resource_monitor = ResourceMonitor(metrics=metrics, config=config)
    await resource_monitor.start()
    
    resource_status = await resource_monitor.check_health()
    print("시스템 리소스:", resource_status)
    
    # 5. 메트릭 기록 테스트
    metrics.increment_requests("test_api", "GET", "success")
    metrics.record_latency("test_api", "GET", 0.1)
    
    # 6. 기록된 메트릭 확인
    all_metrics = await metrics.export_metrics()
    print("\n기록된 메트릭:", all_metrics)
    
    # 7. 정리
    await api_monitor.stop()
    await resource_monitor.stop()

if __name__ == "__main__":
    asyncio.run(test_system())