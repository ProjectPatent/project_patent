# monitoring/__init__.py

"""
IP Rights 모니터링 패키지

이 패키지는 산업재산권 데이터의 수집, 분석, 모니터링을 위한 도구들을 제공합니다.
"""

__version__ = "1.0.0"

# alerts 모듈
from .alerts.manager import (
    AlertManager,
    Alert,
    AlertSeverity
)
from .alerts.handlers import (
    AlertHandler,
    SlackAlertHandler,
    EmailAlertHandler
)

# core 모듈
from .core.metrics import (
    IPRMetrics,
    MetricConfig
)
from .core.config import MonitoringConfig
from .core.base import BaseMonitor
from .core.decorators import monitor_api_call
from .core.exceptions import (
    MonitoringError,
    MetricError,
    ConfigurationError,
    ValidationError
)

# exporters 모듈
from .exporters.prometheus import (
    PrometheusExporter,
    PrometheusExporterError
)
from .exporters.formatters import (
    MetricFormatter,
    BaseFormatter,
    JsonFormatter,
    TextFormatter,
    FormatterError
)

# monitors 모듈
from .monitors.api_monitor import (
    APIMonitor,
    APIMonitorError
)
from .monitors.resource_monitor import (
    ResourceMonitor,
    ResourceMonitorError
)
from .monitors.health_monitor import (
    HealthMonitor,
    HealthMonitorError
)

# utils 모듈
from .utils.packet_parser import (
    PacketParser,
    PacketParserError
)
from .utils.protocol_monitor import (
    ProtocolMonitor,
    ProtocolMonitorError
)
from .utils.rate_limiter import (
    RateLimiter,
    RateLimitError
)
from .utils.traffic_capture import (
    TrafficCapture,
    TrafficCaptureError
)
from .utils.validators import Validators

# 패키지 메타데이터
__author__ = "IP Rights Monitoring Team"
__email__ = "support@organization.com"
__description__ = "Industrial Property Rights Monitoring System"

# 사용자에게 제공할 공개 인터페이스
__all__ = [
    # Base classes
    "BaseMonitor",
    "AlertHandler",
    "BaseFormatter",
    
    # Managers and Core Components
    "AlertManager",
    "Alert",
    "AlertSeverity",
    "IPRMetrics",
    "MetricConfig",
    "MonitoringConfig",
    
    # Handlers
    "SlackAlertHandler",
    "EmailAlertHandler",
    
    # Monitors
    "APIMonitor",
    "ResourceMonitor",
    "HealthMonitor",
    "ProtocolMonitor",
    "TrafficCapture",
    
    # Exporters
    "PrometheusExporter",
    "MetricFormatter",
    "JsonFormatter",
    "TextFormatter",
    
    # Utils
    "PacketParser",
    "RateLimiter",
    "Validators",
    
    # Decorators
    "monitor_api_call",
    
    # Exceptions
    "MonitoringError",
    "MetricError",
    "ConfigurationError",
    "ValidationError",
    "PrometheusExporterError",
    "APIMonitorError",
    "ResourceMonitorError",
    "HealthMonitorError",
    "PacketParserError",
    "ProtocolMonitorError",
    "RateLimitError",
    "TrafficCaptureError",
    "FormatterError"
]