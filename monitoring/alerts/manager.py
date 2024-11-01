# alerts/manager.py
from enum import Enum
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
from monitoring.core.metrics import (
    alert_count,
    alert_send_failures,
    alert_history_size
)

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """알림 심각도 정의"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """알림 데이터 클래스"""
    title: str
    message: str
    severity: AlertSeverity
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """유효성 검증 및 메트릭 업데이트"""
        if not self.title or not self.message:
            raise ValueError("Alert must have both title and message")
        alert_count.labels(severity=self.severity.value).inc()

class AlertManager:
    """알림 관리 클래스"""
    
    def __init__(self, max_history: int = 1000):
        self.handlers: Dict[str, AlertHandler] = {}
        self.alert_history: List[Alert] = []
        self.max_history = max_history
        self._failed_handlers: Set[str] = set()
        logger.info(f"AlertManager initialized with max_history={max_history}")
        
    def register_handler(self, name: str, handler: AlertHandler):
        """알림 핸들러 등록"""
        if name in self.handlers:
            logger.warning(f"Overwriting existing handler: {name}")
        self.handlers[name] = handler
        logger.info(f"Registered alert handler: {name}")
        
    def remove_handler(self, name: str):
        """알림 핸들러 제거"""
        if name in self.handlers:
            del self.handlers[name]
            logger.info(f"Removed alert handler: {name}")
            
    async def send_alert(
        self, 
        alert: Alert, 
        handlers: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        알림을 지정된 핸들러들에게 전송
        
        Args:
            alert: 전송할 알림 객체
            handlers: 사용할 핸들러 이름 목록 (None이면 모든 핸들러 사용)
            
        Returns:
            Dict[str, bool]: 핸들러별 전송 결과
        """
        results = {}
        target_handlers = self._get_target_handlers(handlers)
        
        for name, handler in target_handlers.items():
            try:
                results[name] = await handler.send_alert(alert)
                if not results[name]:
                    self._handle_failure(name)
            except Exception as e:
                logger.error(
                    f"Error sending alert through {name}: {str(e)}",
                    exc_info=True
                )
                results[name] = False
                self._handle_failure(name)
                
        self._add_to_history(alert)
        return results
    
    def _get_target_handlers(
        self, 
        handlers: Optional[List[str]] = None
    ) -> Dict[str, AlertHandler]:
        """지정된 핸들러 또는 전체 핸들러 반환"""
        if handlers:
            return {
                name: handler 
                for name, handler in self.handlers.items() 
                if name in handlers
            }
        return self.handlers
    
    def _handle_failure(self, handler_name: str):
        """핸들러 실패 처리"""
        alert_send_failures.labels(handler=handler_name).inc()
        self._failed_handlers.add(handler_name)
    
    def _add_to_history(self, alert: Alert):
        """알림 히스토리 관리"""
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
        alert_history_size.set(len(self.alert_history))
            
    def get_history(
        self, 
        limit: Optional[int] = None,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """
        알림 히스토리 조회
        
        Args:
            limit: 반환할 최대 알림 수
            severity: 특정 심각도의 알림만 필터링
        """
        history = self.alert_history
        if severity:
            history = [a for a in history if a.severity == severity]
        return history[-limit:] if limit else history.copy()
    
    def clear_history(self):
        """알림 히스토리 초기화"""
        self.alert_history.clear()
        alert_history_size.set(0)
        logger.info("Alert history cleared")

    def get_failed_handlers(self) -> Set[str]:
        """실패한 핸들러 목록 반환"""
        return self._failed_handlers.copy()

    def reset_failed_handlers(self):
        """실패 핸들러 상태 초기화"""
        self._failed_handlers.clear()
        logger.info("Failed handlers status reset")