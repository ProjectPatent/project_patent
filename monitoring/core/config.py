# monitoring/core/config.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import logging
from .exceptions import ConfigurationError, ValidationError

logger = logging.getLogger(__name__)

@dataclass
class Config:
    """기본 설정 클래스"""
    def get_value(self, key: str, default: Any = None) -> Any:
        """설정값 조회"""
        return getattr(self, key, default)
        
    def get_section(self, section: str) -> Dict[str, Any]:
        """설정 섹션 조회"""
        if not hasattr(self, f"{section}_config"):
            raise ConfigurationError(f"Unknown configuration section: {section}")
        return getattr(self, f"{section}_config")

@dataclass
class MonitoringConfig(Config):
    """
    모니터링 전역 설정을 관리하는 클래스.
    
    Attributes:
        service_name (str): 서비스 이름으로, 메트릭 식별에 사용됩니다.
        enabled (bool): 모니터링 활성화 여부 (기본값: True).
        prometheus_port (int): Prometheus 서버 포트 (기본값: 8000).
        check_interval (int): 상태 체크 간격 (초 단위, 기본값: 60).
        log_level (str): 로깅 레벨 (기본값: "INFO").
        slack_webhook_url (str): Slack 웹훅 URL (선택).
        smtp_config (Dict[str, Any]): 이메일 전송 관련 SMTP 설정.
        alert_config (Dict[str, Any]): 알림 관련 설정.
        metric_config (Dict[str, Any]): 메트릭 관련 설정.
    """
    service_name: str
    enabled: bool = True
    prometheus_port: int = 8000
    check_interval: int = 60
    log_level: str = "INFO"
    slack_webhook_url: Optional[str] = None
    smtp_config: Dict[str, Any] = field(default_factory=dict)
    alert_config: Dict[str, Any] = field(default_factory=dict)
    metric_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """설정 초기화 및 유효성 검증."""
        self.validate()
        self._setup_logging()
        
    def validate(self):
        """설정 유효성 검증.
        
        Raises:
            ValidationError: 서비스 이름이 없거나 prometheus 포트가 유효하지 않을 때 발생.
        """
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
        """로깅 설정.
        
        log_level 속성에 지정된 로깅 레벨을 사용하여 기본 로깅 설정을 초기화합니다.
        """
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """설정 섹션 조회.
        
        Args:
            section (str): 조회할 섹션 이름 ("alert", "metric", "smtp" 등).

        Returns:
            Dict[str, Any]: 해당 섹션의 설정 딕셔너리.
        
        Raises:
            ConfigurationError: 잘못된 섹션 이름을 조회할 때 발생.
        """
        sections = {
            'alert': self.alert_config,
            'metric': self.metric_config,
            'smtp': self.smtp_config
        }
        if section not in sections:
            raise ConfigurationError(f"Unknown configuration section: {section}")
        return sections[section]