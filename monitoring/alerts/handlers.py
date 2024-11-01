# alerts/handlers.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import aiohttp
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from monitoring.core.metrics import alert_send_time, alert_send_failures
from monitoring.core.exceptions import AlertError
from monitoring.core.config import Config

logger = logging.getLogger(__name__)

class AlertHandler(ABC):
    """알림 전송을 위한 기본 핸들러 클래스"""
    
    @abstractmethod
    async def send_alert(self, alert: 'Alert') -> bool:
        """알림을 전송하는 추상 메서드"""
        pass
    
    async def _handle_error(self, e: Exception, handler_name: str) -> bool:
        """에러 처리 및 로깅"""
        logger.error(
            f"{handler_name} alert sending failed: {str(e)}", 
            exc_info=True,
            extra={"handler": handler_name, "error": str(e)}
        )
        alert_send_failures.labels(handler=handler_name).inc()
        return False

class SlackAlertHandler(AlertHandler):
    def __init__(self, config: Config):
        """
        Args:
            config: 설정 객체 (webhook_url 필수)
        """
        self.webhook_url = config.get_value("slack_webhook_url")
        if not self.webhook_url:
            raise ValueError("Slack webhook URL is required")
            
        self.timeout = aiohttp.ClientTimeout(
            total=config.get_value("slack_timeout", 10)
        )
    
    @alert_send_time.time()
    async def send_alert(self, alert: 'Alert') -> bool:
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                payload = self._create_payload(alert)
                async with session.post(self.webhook_url, json=payload) as response:
                    if not response.ok:
                        raise AlertError(f"Slack API returned {response.status}")
                    return True
                    
        except Exception as e:
            return await self._handle_error(e, "slack")
            
    def _create_payload(self, alert: 'Alert') -> Dict[str, Any]:
        """Slack 메시지 페이로드 생성"""
        return {
            "text": f"*{alert.title}*\n{alert.message}",
            "attachments": [{
                "color": self._get_color(alert.severity),
                "fields": [
                    {"title": "Severity", "value": alert.severity.value},
                    {"title": "Timestamp", "value": alert.timestamp.isoformat()}
                ] + [
                    {"title": k, "value": str(v)}
                    for k, v in (alert.metadata or {}).items()
                ]
            }]
        }
        
    def _get_color(self, severity: 'AlertSeverity') -> str:
        """알림 심각도에 따른 색상 반환"""
        return {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffcc00", 
            AlertSeverity.ERROR: "#ff9900",
            AlertSeverity.CRITICAL: "#ff0000"
        }.get(severity, "#000000")

class EmailAlertHandler(AlertHandler):
    def __init__(self, config: Config):
        """
        Args:
            config: SMTP 설정을 포함한 설정 객체
        """
        self.smtp_config = config.get_section("smtp")
        self._validate_config()
        
    def _validate_config(self):
        """SMTP 설정 유효성 검증"""
        required = ['host', 'port', 'from_address', 'to_address']
        missing = [field for field in required if field not in self.smtp_config]
        if missing:
            raise ValueError(f"Missing required SMTP config fields: {missing}")
    
    @alert_send_time.time()
    async def send_alert(self, alert: 'Alert') -> bool:
        try:
            msg = self._create_message(alert)
            await self._send_email(msg)
            return True
            
        except Exception as e:
            return await self._handle_error(e, "email")
            
    def _create_message(self, alert: 'Alert') -> MIMEText:
        """이메일 메시지 생성"""
        msg = MIMEText(self._format_message(alert))
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
        msg['From'] = self.smtp_config['from_address']
        msg['To'] = self.smtp_config['to_address']
        return msg
            
    async def _send_email(self, msg: MIMEText):
        """이메일 전송"""
        with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
            if self.smtp_config.get('use_tls', False):
                server.starttls()
            if 'username' in self.smtp_config:
                server.login(
                    self.smtp_config['username'],
                    self.smtp_config['password']
                )
            server.send_message(msg)
            
    def _format_message(self, alert: 'Alert') -> str:
        """이메일 본문 포맷팅"""
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
