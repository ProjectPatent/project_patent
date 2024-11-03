# monitoring/core/exceptions.py
from typing import Any, Dict, Optional

class MonitoringError(Exception):
    """모니터링 과정에서 발생하는 일반적인 예외"""
    def __init__(self, message: str, **context):
        super().__init__(message)
        self.context = context

class AlertError(MonitoringError):
    """알림 전송 과정에서 발생하는 예외"""
    def __init__(self, message: str, handler_name: Optional[str] = None, **context):
        super().__init__(message, handler_name=handler_name, **context)
        self.handler_name = handler_name
        
class MetricError(MonitoringError):
    """메트릭 설정 또는 업데이트 중 발생하는 예외"""
    def __init__(self, message: str, metric_name: Optional[str] = None, **context):
        super().__init__(message, metric_name=metric_name, **context)
        self.metric_name = metric_name

class ConfigurationError(MonitoringError):
    """설정 관련 예외"""
    def __init__(self, message: str, **context):
        super().__init__(message, **context)

class ValidationError(MonitoringError):
    """데이터 유효성 검사 실패 예외"""
    def __init__(self, message: str, field_name: str, invalid_value: Any, validation_rule: str):
        super().__init__(
            message, 
            field_name=field_name, 
            invalid_value=invalid_value, 
            validation_rule=validation_rule
        )
        self.field_name = field_name
        self.invalid_value = invalid_value
        self.validation_rule = validation_rule