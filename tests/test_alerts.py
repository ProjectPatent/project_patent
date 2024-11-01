# tests/test_alerts.py
from unittest.mock import Mock, patch
import pytest
from monitoring.alerts import AlertManager, SlackAlertHandler, EmailAlertHandler

@pytest.fixture
def mock_config():
    config = Mock()
    config.get_value.return_value = "http://mock-webhook.url"
    config.get_section.return_value = {
        "host": "smtp.test.com",
        "port": 587,
        "from_address": "test@test.com",
        "to_address": "admin@test.com"
    }
    return config

@pytest.mark.asyncio
async def test_slack_alert_handler(mock_config):
    handler = SlackAlertHandler(mock_config)
    alert = Alert(
        title="Test Alert",
        message="Test Message",
        severity=AlertSeverity.WARNING
    )
    
    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = Mock()
        mock_response.ok = True
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        result = await handler.send_alert(alert)
        assert result is True