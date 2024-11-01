# tests/test_alerts.py
import pytest
from unittest.mock import Mock, patch
import aiohttp
from monitoring.alerts.handlers import SlackAlertHandler, EmailAlertHandler
from monitoring.core.exceptions import AlertError

@pytest.mark.asyncio
async def test_alert_manager_send_alert(alert_manager, mock_alert):
    """알림 매니저 send_alert 테스트"""
    mock_handler = Mock()
    mock_handler.send_alert.return_value = True
    
    alert_manager.register_handler("test", mock_handler)
    results = await alert_manager.send_alert(mock_alert)
    
    assert "test" in results
    assert results["test"] is True
    assert len(alert_manager.alert_history) == 1

@pytest.mark.asyncio
async def test_slack_handler(mock_config, mock_alert):
    """Slack 알림 핸들러 테스트"""
    mock_config.slack_webhook_url = "http://test.webhook"
    handler = SlackAlertHandler(mock_config)
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = Mock()
        mock_response.ok = True
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        result = await handler.send_alert(mock_alert)
        assert result is True

@pytest.mark.asyncio
async def test_email_handler(mock_config, mock_alert):
    """이메일 알림 핸들러 테스트"""
    mock_config.smtp_config = {
        'host': 'localhost',
        'port': 25,
        'from_address': 'test@test.com',
        'to_address': 'admin@test.com'
    }
    handler = EmailAlertHandler(mock_config)
    
    with patch('smtplib.SMTP') as mock_smtp:
        result = await handler.send_alert(mock_alert)
        assert result is True
