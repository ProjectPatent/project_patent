# tests/test_handlers.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, UTC
import aiohttp
import smtplib
from email.mime.text import MIMEText

from monitoring.alerts.handlers import (
    AlertHandler,
    SlackAlertHandler,
    EmailAlertHandler
)
from monitoring.alerts.manager import Alert, AlertSeverity
from monitoring.core.config import Config
from monitoring.core.exceptions import AlertError

@pytest.fixture
def mock_config():
    """테스트용 설정 객체"""
    config = Mock(spec=Config)
    config.get_value.return_value = "http://test.webhook.url"
    config.get_section.return_value = {
        'host': 'smtp.test.com',
        'port': 587,
        'from_address': 'from@test.com',
        'to_address': 'to@test.com',
        'username': 'testuser',
        'password': 'testpass',
        'use_tls': True
    }
    return config

@pytest.fixture
def mock_metrics():
    """테스트용 메트릭 객체"""
    metrics = Mock()
    metrics.alert_send_time = Mock()
    metrics.alert_send_time.labels.return_value = Mock()
    metrics.alert_send_failures = Mock()
    metrics.alert_send_failures.labels.return_value = Mock()
    return metrics

@pytest.fixture
def test_alert():
    """테스트용 알림 객체"""
    return Alert(
        title="Test Alert",
        message="Test Message",
        severity=AlertSeverity.WARNING,
        timestamp=datetime.now(UTC),
        metadata={"test_key": "test_value"}
    )

# Slack 핸들러 테스트
class TestSlackAlertHandler:
    @pytest.mark.asyncio
    async def test_slack_handler_success(self, mock_config, mock_metrics, test_alert):
        """Slack 알림 전송 성공 테스트"""
        handler = SlackAlertHandler(config=mock_config, metrics=mock_metrics)
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = Mock()
            mock_response.ok = True
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await handler.send_alert(test_alert)
            
            assert result is True
            mock_post.assert_called_once()
            assert mock_metrics.alert_send_time.labels.called
    
    @pytest.mark.asyncio
    async def test_slack_handler_error(self, mock_config, mock_metrics, test_alert):
        """Slack 알림 전송 실패 테스트"""
        handler = SlackAlertHandler(config=mock_config, metrics=mock_metrics)
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = aiohttp.ClientError("Test error")
            
            result = await handler.send_alert(test_alert)
            
            assert result is False
            assert mock_metrics.alert_send_failures.labels.called

    def test_slack_payload_format(self, mock_config, test_alert):
        """Slack 메시지 페이로드 포맷 테스트"""
        handler = SlackAlertHandler(config=mock_config)
        payload = handler._create_payload(test_alert)
        
        assert isinstance(payload, dict)
        assert "*Test Alert*" in payload["text"]
        assert "Test Message" in payload["text"]
        assert len(payload["attachments"]) == 1
        
        fields = payload["attachments"][0]["fields"]
        assert any(field["title"] == "Severity" for field in fields)
        assert any(field["title"] == "test_key" for field in fields)

# Email 핸들러 테스트
class TestEmailAlertHandler:
    @pytest.mark.asyncio
    async def test_email_handler_success(self, mock_config, mock_metrics, test_alert):
        """이메일 전송 성공 테스트"""
        handler = EmailAlertHandler(config=mock_config, metrics=mock_metrics)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.return_value.__enter__.return_value = Mock()
            
            result = await handler.send_alert(test_alert)
            
            assert result is True
            assert mock_smtp.called
            assert mock_metrics.alert_send_time.labels.called

    @pytest.mark.asyncio
    async def test_email_handler_error(self, mock_config, mock_metrics, test_alert):
        """이메일 전송 실패 테스트"""
        handler = EmailAlertHandler(config=mock_config, metrics=mock_metrics)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = smtplib.SMTPException("Test error")
            
            result = await handler.send_alert(test_alert)
            
            assert result is False
            assert mock_metrics.alert_send_failures.labels.called

    def test_email_message_format(self, mock_config, test_alert):
        """이메일 메시지 포맷 테스트"""
        handler = EmailAlertHandler(config=mock_config)
        msg = handler._create_message(test_alert)
        
        assert isinstance(msg, MIMEText)
        assert f"[{test_alert.severity.value.upper()}]" in msg['Subject']
        assert test_alert.title in msg['Subject']
        assert test_alert.message in msg.get_payload()
        assert "test_key: test_value" in msg.get_payload()