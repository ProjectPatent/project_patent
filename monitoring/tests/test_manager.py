import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from monitoring.alerts.manager import AlertManager, Alert, AlertSeverity

@pytest.fixture
def alert_manager():
    return AlertManager(max_history=5)

@pytest.fixture
def sample_alert():
    return Alert(
        title="Test Alert",
        message="This is a test alert",
        severity=AlertSeverity.WARNING,
        timestamp=datetime.now(timezone.utc)
    )

@pytest.mark.asyncio
async def test_initial_state(alert_manager):
    assert alert_manager.handlers == {}
    assert alert_manager.alert_history == []

def test_register_handler(alert_manager):
    mock_handler = AsyncMock()
    alert_manager.register_handler("mock", mock_handler)
    assert "mock" in alert_manager.handlers
    assert alert_manager.handlers["mock"] == mock_handler

def test_register_handler_duplicate(alert_manager, caplog):
    mock_handler = AsyncMock()
    alert_manager.register_handler("mock", mock_handler)
    alert_manager.register_handler("mock", mock_handler)
    assert "mock" in alert_manager.handlers
    assert sum(record.levelname == "WARNING" for record in caplog.records) == 1

def test_remove_handler(alert_manager):
    mock_handler = AsyncMock()
    alert_manager.register_handler("mock", mock_handler)
    alert_manager.remove_handler("mock")
    assert "mock" not in alert_manager.handlers

@pytest.mark.asyncio
async def test_send_alert_success(alert_manager, sample_alert):
    mock_handler = AsyncMock()
    mock_handler.send_alert.return_value = True
    alert_manager.register_handler("mock", mock_handler)
    results = await alert_manager.send_alert(sample_alert)
    assert results == {"mock": True}
    mock_handler.send_alert.assert_awaited_once_with(sample_alert)
    assert alert_manager.alert_history == [sample_alert]

@pytest.mark.asyncio
async def test_send_alert_failure(alert_manager, sample_alert):
    mock_handler = AsyncMock()
    mock_handler.send_alert.return_value = False
    alert_manager.register_handler("mock", mock_handler)
    results = await alert_manager.send_alert(sample_alert)
    assert results == {"mock": False}
    assert "mock" in alert_manager.get_failed_handlers()

def test_alert_history_limit(alert_manager, sample_alert):
    for _ in range(10):
        alert_manager._add_to_history(sample_alert)
    assert len(alert_manager.alert_history) == alert_manager.max_history

def test_get_failed_handlers(alert_manager):
    alert_manager._failed_handlers.add("mock")
    failed_handlers = alert_manager.get_failed_handlers()
    assert failed_handlers == {"mock"}

def test_reset_failed_handlers(alert_manager):
    alert_manager._failed_handlers.add("mock")
    alert_manager.reset_failed_handlers()
    assert alert_manager._failed_handlers == set()