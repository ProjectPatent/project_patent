# tests/test_metrics.py
import pytest
from monitoring.core.metrics import IPRMetrics, MetricConfig

class TestIPRMetrics:
    @pytest.fixture
    def metrics(self):
        return IPRMetrics(
            service_name='test',
            config=MetricConfig(prefix='test_')
        )
    
    def test_metric_initialization(self, metrics):
        assert metrics.service_name == 'test'
        assert metrics.api_requests._name.startswith('test_')
        
    @pytest.mark.asyncio
    async def test_api_request_tracking(self, metrics):
        initial = metrics.api_requests.collect()[0].samples[0].value
        metrics.api_requests.labels(
            endpoint='test',
            method='GET',
            status='success'
        ).inc()
        after = metrics.api_requests.collect()[0].samples[0].value
        assert after == initial + 1