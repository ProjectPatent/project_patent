# tests/test_alerts.py
import pytest
from unittest.mock import Mock, patch
import aiohttp
from monitoring.alerts import (
    AlertManager, 
    Alert,
    AlertSeverity,
    SlackAlertHandler,
    EmailAlertHandler
)
from monitoring.core.exceptions import AlertError

@pytest.mark.asyncio
async def test_alert_manager_initialization(alert_manager):
    """AlertManager 초기화 테스트"""
    assert alert_manager.handlers == {}
    assert alert_manager.alert_history == []
    assert alert_manager.max_history == 10

@pytest.mark.asyncio
async def test_alert_creation(mock_alert):
    """Alert 객체 생성 테스트"""
    assert mock_alert.title == "Test Alert"
    assert mock_alert.message == "Test Message"
    assert mock_alert.severity == AlertSeverity.WARNING
    assert mock_alert.metadata == {"test_key": "test_value"}

@pytest.mark.asyncio
async def test_slack_handler(mock_slack_handler, mock_alert):
    """Slack 핸들러 테스트"""
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value.__aenter__.return_value = mock_response
        
        result = await mock_slack_handler.send_alert(mock_alert)
        assert result is True
        
        # webhook URL로 요청이 전송되었는지 확인
        mock_post.assert_called_once()
        
        

@pytest.mark.asyncio
async def test_email_handler(mock_email_handler, mock_alert):
    """Email 핸들러 테스트"""
    with patch('smtplib.SMTP') as mock_smtp:
        # SMTP 서버 연결 성공 시뮬레이션
        mock_smtp.return_value.__enter__.return_value = Mock()
        
        result = await mock_email_handler.send_alert(mock_alert)
        assert result is True
        
        # SMTP 서버로 메일이 전송되었는지 확인
        mock_smtp.assert_called_once_with('localhost', 25)

@pytest.mark.asyncio
async def test_alert_manager_with_handlers(alert_manager, mock_slack_handler, mock_email_handler, mock_alert):
    """AlertManager와 핸들러 통합 테스트"""
    # 핸들러 등록
    alert_manager.register_handler("slack", mock_slack_handler)
    alert_manager.register_handler("email", mock_email_handler)
    
    with patch('aiohttp.ClientSession.post') as mock_post, \
         patch('smtplib.SMTP') as mock_smtp:
        # 성공 응답 시뮬레이션
        mock_post.return_value.__aenter__.return_value.ok = True
        mock_smtp.return_value.__enter__.return_value = Mock()
        
        # 알림 전송
        results = await alert_manager.send_alert(mock_alert)
        
        # 결과 확인
        assert results["slack"] is True
        assert results["email"] is True
        assert len(alert_manager.alert_history) == 1

@pytest.mark.asyncio
async def test_alert_error_handling(alert_manager, mock_slack_handler, mock_alert):
    """에러 처리 테스트"""
    alert_manager.register_handler("slack", mock_slack_handler)
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        # 실패 응답 시뮬레이션
        mock_post.return_value.__aenter__.return_value.ok = False
        mock_post.return_value.__aenter__.return_value.status = 500
        
        results = await alert_manager.send_alert(mock_alert)
        assert results["slack"] is False
        assert "slack" in alert_manager.get_failed_handlers()

@pytest.mark.asyncio
async def test_metrics_recording(mock_metrics, alert_manager, mock_slack_handler, mock_alert):
    """메트릭 기록 테스트"""
    # AlertManager에 메트릭 설정
    alert_manager.metrics = mock_metrics
    mock_slack_handler.metrics = mock_metrics
    
    alert_manager.register_handler("slack", mock_slack_handler)
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.return_value.__aenter__.return_value.ok = True
        
        await alert_manager.send_alert(mock_alert)
        
        # 메트릭이 기록되었는지 확인
        metrics_data = await mock_metrics.export_metrics()
        
        # 알림 총 개수 메트릭 확인
        assert "test_service_alerts_total" in metrics_data
        
        # 알림 전송 시간 메트릭 확인 (Summary 타입은 _count와 _created 접미사를 가짐)
        assert "test_service_alert_send_duration_seconds_count" in metrics_data
        assert "test_service_alert_send_duration_seconds_created" in metrics_data
        
        # 알림 히스토리 크기 확인
        assert metrics_data["test_service_alert_history_size"] == 1.0

@pytest.mark.asyncio
async def test_alert_history_management(alert_manager, mock_alert):
    """알림 히스토리 관리 테스트"""
    # 최대 히스토리 크기보다 많은 알림 추가
    for _ in range(15):  # max_history는 10
        alert_manager._add_to_history(mock_alert)
    
    # 히스토리 크기 확인
    assert len(alert_manager.alert_history) == 10
    
    # 히스토리 조회 테스트
    history = alert_manager.get_history(limit=5)
    assert len(history) == 5
    
    # 심각도 기준 필터링 테스트
    warning_history = alert_manager.get_history(severity=AlertSeverity.WARNING)
    assert all(alert.severity == AlertSeverity.WARNING for alert in warning_history)