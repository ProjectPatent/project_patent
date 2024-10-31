from abc import ABC, abstractmethod
from typing import Dict, Any
import aiohttp
import smtplib
import logging
from email.mime.text import MIMEText
from .manager import Alert, AlertManager, AlertSeverity

class AlertHandler(ABC):
    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """알림을 전송하는 추상 메서드"""
        pass

class SlackAlertHandler(AlertHandler):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        
    async def send_alert(self, alert: Alert) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "text": f"*{alert.title}*\n{alert.message}",
                    "attachments": [{
                        "color": self._get_color(alert.severity),
                        "fields": [
                            {"title": "Severity", "value": alert.severity.value},
                            {"title": "Timestamp", "value": alert.timestamp.isoformat()}
                        ]
                    }]
                }
                if alert.metadata:
                    payload["attachments"][0]["fields"].extend(
                        [{"title": k, "value": str(v)} for k, v in alert.metadata.items()]
                    )
                    
                async with session.post(self.webhook_url, json=payload) as response:
                    return response.status == 200
        except Exception as e:
            logging.error(f"Slack alert sending failed: {str(e)}")
            return False
            
    def _get_color(self, severity: AlertSeverity) -> str:
        return {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffcc00",
            AlertSeverity.ERROR: "#ff9900",
            AlertSeverity.CRITICAL: "#ff0000"
        }.get(severity, "#000000")

class EmailAlertHandler(AlertHandler):
    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_config = smtp_config
        
    async def send_alert(self, alert: Alert) -> bool:
        try:
            msg = MIMEText(self._format_message(alert))
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            msg['From'] = self.smtp_config['from_address']
            msg['To'] = self.smtp_config['to_address']
            
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config.get('use_tls', False):
                    server.starttls()
                if 'username' in self.smtp_config:
                    server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            return True
        except Exception as e:
            logging.error(f"Email alert sending failed: {str(e)}")
            return False
            
    def _format_message(self, alert: Alert) -> str:
        message = f"""
Alert Details:
-------------
Severity: {alert.severity.value}
Time: {alert.timestamp.isoformat()}
Message: {alert.message}
"""
        if alert.metadata:
            message += "\nAdditional Information:\n"
            for k, v in alert.metadata.items():
                message += f"{k}: {v}\n"
        return message