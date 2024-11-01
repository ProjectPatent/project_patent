# formatters.py
import json
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from ..core.exceptions import MonitoringError

logger = logging.getLogger(__name__)

class FormatterError(MonitoringError):
    """포맷터 관련 예외"""
    def __init__(self, message: str, format_type: str, **context):
        super().__init__(message, format_type=format_type, **context)
        self.format_type = format_type

class BaseFormatter(ABC):
    """기본 포맷터 클래스"""
    
    @abstractmethod
    def format(self, metrics: Dict[str, Any]) -> str:
        """메트릭 포맷팅"""
        pass

class JsonFormatter(BaseFormatter):
    """JSON 포맷터"""
    
    def __init__(self, indent: int = 2):
        self.indent = indent
    
    def format(self, metrics: Dict[str, Any]) -> str:
        try:
            return json.dumps(metrics, indent=self.indent)
        except TypeError as e:
            logger.error(f"JSON formatting failed: {str(e)}", exc_info=True)
            raise FormatterError(
                "Failed to format metrics as JSON",
                format_type="json",
                error=str(e)
            ) from e

class TextFormatter(BaseFormatter):
    """텍스트 포맷터"""
    
    def __init__(self, separator: str = "\n"):
        self.separator = separator
    
    def format(self, metrics: Dict[str, Any]) -> str:
        try:
            lines = [f"{name}: {value}" for name, value in metrics.items()]
            return self.separator.join(lines)
        except Exception as e:
            logger.error(f"Text formatting failed: {str(e)}", exc_info=True)
            raise FormatterError(
                "Failed to format metrics as text",
                format_type="text",
                error=str(e)
            ) from e

class MetricFormatter:
    """통합 메트릭 포맷터"""
    
    def __init__(self):
        self._formatters = {
            'json': JsonFormatter(),
            'text': TextFormatter()
        }
    
    def format(self, metrics: Dict[str, Any], format_type: str = 'json') -> str:
        """메트릭을 지정된 형식으로 변환"""
        formatter = self._formatters.get(format_type)
        if not formatter:
            raise FormatterError(
                "Unsupported format type",
                format_type=format_type,
                supported_formats=list(self._formatters.keys())
            )
            
        return formatter.format(metrics)
    
    def register_formatter(self, name: str, formatter: BaseFormatter):
        """새로운 포맷터 등록"""
        if not isinstance(formatter, BaseFormatter):
            raise TypeError("Formatter must be an instance of BaseFormatter")
        self._formatters[name] = formatter
        logger.info(f"Registered new formatter: {name}")
