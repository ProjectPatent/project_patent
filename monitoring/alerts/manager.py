# alerts/manager.py
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Alert:
    title: str
    message: str
    severity: str = 'info'
    metadata: Optional[Dict[str, Any]] = None

class AlertManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.handlers = []
        
    def add_handler(self, handler):
        self.handlers.append(handler)
        
    async def send_alert(self, alert: Alert):
        for handler in self.handlers:
            try:
                await handler.send_alert(alert)
            except Exception as e:
                self.logger.error(f"Failed to send alert: {e}")