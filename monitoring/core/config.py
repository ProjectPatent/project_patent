# config.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import logging
from .exceptions import ConfigurationError, ValidationError

logger = logging.getLogger(__name__)

@dataclass
class MonitoringConfig:
    """모니터링 전역 설정"""
    service_name: str
    enabled: bool = True
    prometheus_port: int = 8000
    check_interval: int = 60
    log_level: str = "INFO"
    alert_config: Dict[str, Any] = field(default_factory=dict)
    metric_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """설정 초기화 및 유효성 검증"""
        self.validate()
        self._setup_logging()
        
    def validate(self):
        """설정 유효성 검증"""
        if not self.service_name:
            raise ValidationError(
                "Service name cannot be empty",
                field_name="service_name",
                invalid_value=self.service_name,
                validation_rule="non-empty string required"
            )
        if self.prometheus_port < 0 or self.prometheus_port > 65535:
            raise ValidationError(
                "Invalid prometheus port",
                field_name="prometheus_port",
                invalid_value=self.prometheus_port,
                validation_rule="0 <= port <= 65535"
            )
        
    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """설정값 조회"""
        return getattr(self, key, default)
        
    def get_section(self, section: str) -> Dict[str, Any]:
        """설정 섹션 조회"""
        sections = {
            'alert': self.alert_config,
            'metric': self.metric_config
        }
        if section not in sections:
            raise ConfigurationError(f"Unknown configuration section: {section}")
        return sections[section]