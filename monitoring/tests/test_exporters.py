# tests/test_exporters.py
import pytest
from monitoring.exporters.formatters import MetricFormatter
from monitoring.exporters.prometheus import PrometheusExporter

def test_metric_formatter():
    """메트릭 포맷터 테스트"""
    formatter = MetricFormatter()
    test_metrics = {
        "test_counter": 10,
        "test_gauge": 5.5
    }
    
    # JSON 포맷 테스트
    json_result = formatter.format(test_metrics, 'json')
    assert isinstance(json_result, str)
    assert "test_counter" in json_result
    
    # 텍스트 포맷 테스트
    text_result = formatter.format(test_metrics, 'text')
    assert isinstance(text_result, str)
    assert "test_counter: 10" in text_result

@pytest.mark.asyncio
async def test_prometheus_exporter(mock_metrics, mock_prometheus_registry):
    """Prometheus 익스포터 테스트"""
    exporter = PrometheusExporter(
        metrics=mock_metrics,
        port=8001,
        registry=mock_prometheus_registry
    )
    
    await exporter.start()
    assert exporter.is_running is True
    
    await exporter.stop()
    assert exporter.is_running is False
