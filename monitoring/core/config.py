from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class MonitoringConfig:
    """모니터링 전역 설정"""
    service_name: str
    enabled: bool = True
    prometheus_port: int = 8000
    check_interval: int = 60
    alert_config: Optional[Dict[str, Any]] = None
    metric_config: Optional[Dict[str, Any]] = None
    
    def validate(self):
        """설정 유효성 검증"""
        if not self.service_name:
            raise ConfigurationError("service_name must be specified")
        if self.prometheus_port < 0:
            raise ConfigurationError("Invalid prometheus_port")