from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import logging

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    title: str
    message: str
    severity: AlertSeverity
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class AlertManager:
    def __init__(self):
        self.handlers: Dict[str, AlertHandler] = {}
        self.alert_history: List[Alert] = []
        self.max_history = 1000
        
    def register_handler(self, name: str, handler: AlertHandler):
        """새로운 알림 핸들러 등록"""
        self.handlers[name] = handler
        
    def remove_handler(self, name: str):
        """등록된 알림 핸들러 제거"""
        if name in self.handlers:
            del self.handlers[name]
            
    async def send_alert(self, alert: Alert, handlers: Optional[List[str]] = None) -> Dict[str, bool]:
        """알림을 지정된 핸들러들에게 전송"""
        results = {}
        target_handlers = (
            {name: handler for name, handler in self.handlers.items() if name in handlers}
            if handlers
            else self.handlers
        )
        
        for name, handler in target_handlers.items():
            results[name] = await handler.send_alert(alert)
            
        self._add_to_history(alert)
        return results
    
    def _add_to_history(self, alert: Alert):
        """알림 히스토리에 추가하고 최대 개수 유지"""
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
            
    def get_history(self, limit: Optional[int] = None) -> List[Alert]:
        """알림 히스토리 조회"""
        return self.alert_history[-limit:] if limit else self.alert_history.copy()
    
    def clear_history(self):
        """알림 히스토리 초기화"""
        self.alert_history.clear()