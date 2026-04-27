"""
Integration Tests for SMTP Email Service

Tests complete email sending workflow with realistic mocked SMTP server responses.
Verifies email creation, attachment handling, and SMTP interaction.
"""

import os
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw==")

from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch, mock_open
from uuid import uuid4
import smtplib
import pytest

from src.models.campaign import Campaign, CampaignStatus, CampaignConfig
from src.services.email_service import EmailService


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def email_service():
    """Email service instance"""
    return EmailService(
        sender_email="sender@gmail.com",
        smtp_password="app_password_123"
    )


@pytest.fixture
def completed_campaign():
    """Completed campaign for email notification"""
    config = CampaignConfig(
        profiles=["elonmusk", "naval"],
        keywords=[],
        language="en",
        min_likes=100,
        min_retweets=50,
        min_replies=10,
        hours_back=24
    )
    
    return Campaign(
        id=uuid4(),
        name="AI Trends Analysis",
        social_network="twitter",
        search_type="profile",
        status=CampaignStatus.COMPLETED,
        config=config,
        results_count=150,
        document_url="https://storage.example.com/doc.docx",
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
        completed_at=datetime.now(tz=timezone.utc)
    )


@pytest.fixture
def failed_campaign():
    """Failed campaign for error notification"""
    config = CampaignConfig(
        profiles=["testuser"],
        keywords=[],
        language="en",
        min_likes=10,
        min_retweets=5,
        min_replies=2,
        hours_back=24
    )
    
    return Campaign(
        id=uuid4(),
        name="Failed Campaign",
        social_network="twitter",
        search_type="profile",
        status=CampaignStatus.FAILED,
        config=config,
        results_count=0,
        error_message="API rate limit exceeded",
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
        completed_at=None
    )


# ─── Test Complete Email Sending Workflow ────────────────────────────────────


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_complete_email_sending_workflow(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test complete email sending workflow with attachment"""
    mock_exists.return_value = True
    
    # Mock SMTP server
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    # Send email
    email_service.send_campaign_results(
        "recipient@example.com",
        completed_campaign,
        "/tmp/results.docx"
    )
    
    # Verify SMTP connection
    mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
    
    # Verify STARTTLS was used
    mock_server.starttls.assert_called_once()
    
    # Verify authentication
    mock_server.login.assert_called_once_with("sender@gmail.com", "app_password_123")
    
    # Verify email was sent
    mock_server.send_message.assert_called_once()
    
    # Verify file was opened for attachment
    mock_file.assert_called_once_with("/tmp/results.docx", "rb")


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_email_message_structure(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test that email message has correct structure"""
    mock_exists.return_value = True
    
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    email_service.send_campaign_results(
        "recipient@example.com",
        completed_campaign,
        "/tmp/results.docx"
    )
    
    # Get the message that was sent
    sent_message = mock_server.send_message.call_args[0][0]
    
    # Verify headers
    assert sent_message["From"] == "sender@gmail.com"
    assert sent_message["To"] == "recipient@example.com"
    assert "AI Trends Analysis" in sent_message["Subject"]
    assert "Campaign Results" in sent_message["Subject"]
    
    # Verify message has multiple parts (body + attachment)
    assert len(sent_message.get_payload()) > 1


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_email_body_content(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test that email body contains campaign information"""
    mock_exists.return_value = True
    
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    email_service.send_campaign_results(
        "recipient@example.com",
        completed_campaign,
        "/tmp/results.docx"
    )
    
    sent_message = mock_server.send_message.call_args[0][0]
    message_str = str(sent_message)
    
    # Verify campaign details are in body
    assert "AI Trends Analysis" in message_str
    assert "150" in message_str  # results_count
    assert "COMPLETED" in message_str or "completed" in message_str


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_email_attachment_handling(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test that document is properly attached to email"""
    mock_exists.return_value = True
    
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    email_service.send_campaign_results(
        "recipient@example.com",
        completed_campaign,
        "/tmp/campaign_results.docx"
    )
    
    sent_message = mock_server.send_message.call_args[0][0]
    message_str = str(sent_message)
    
    # Verify attachment is present
    assert "campaign_results.docx" in message_str
    assert "Content-Disposition" in message_str
    assert "attachment" in message_str


# ─── Test Error Scenarios ────────────────────────────────────────────────────


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_smtp_authentication_failure(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test handling of SMTP authentication failure"""
    mock_exists.return_value = True
    
    mock_server = MagicMock()
    mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    with pytest.raises(RuntimeError) as exc_info:
        email_service.send_campaign_results(
            "recipient@example.com",
            completed_campaign,
            "/tmp/results.docx"
        )
    
    assert "authentication" in str(exc_info.value).lower()


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_smtp_connection_error(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test handling of SMTP connection errors"""
    mock_exists.return_value = True
    
    mock_smtp.side_effect = smtplib.SMTPConnectError(421, "Cannot connect to SMTP server")
    
    with pytest.raises(Exception):
        email_service.send_campaign_results(
            "recipient@example.com",
            completed_campaign,
            "/tmp/results.docx"
        )


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_smtp_send_failure(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test handling of email send failure"""
    mock_exists.return_value = True
    
    mock_server = MagicMock()
    mock_server.send_message.side_effect = smtplib.SMTPException("Failed to send email")
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    with pytest.raises(RuntimeError) as exc_info:
        email_service.send_campaign_results(
            "recipient@example.com",
            completed_campaign,
            "/tmp/results.docx"
        )
    
    assert "failed to send" in str(exc_info.value).lower()


@patch('smtplib.SMTP')
@patch('os.path.exists')
def test_missing_attachment_file(
    mock_exists,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test handling of missing attachment file"""
    mock_exists.return_value = False
    
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    # Should still send email without attachment (graceful degradation)
    email_service.send_campaign_results(
        "recipient@example.com",
        completed_campaign,
        "/tmp/nonexistent.docx"
    )
    
    # Email should still be sent
    mock_server.send_message.assert_called_once()


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_smtp_timeout_error(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test handling of SMTP timeout"""
    mock_exists.return_value = True
    
    mock_server = MagicMock()
    mock_server.send_message.side_effect = TimeoutError("SMTP timeout")
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    with pytest.raises(Exception):
        email_service.send_campaign_results(
            "recipient@example.com",
            completed_campaign,
            "/tmp/results.docx"
        )


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_invalid_recipient_email(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test handling of invalid recipient email"""
    mock_exists.return_value = True
    
    mock_server = MagicMock()
    mock_server.send_message.side_effect = smtplib.SMTPRecipientsRefused({
        "invalid@": (550, "Invalid recipient")
    })
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    with pytest.raises(Exception):
        email_service.send_campaign_results(
            "invalid@",
            completed_campaign,
            "/tmp/results.docx"
        )


# ─── Test Email Content Variations ───────────────────────────────────────────


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_email_with_high_results_count(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test email content with high results count"""
    mock_exists.return_value = True
    completed_campaign.results_count = 5000
    
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    email_service.send_campaign_results(
        "recipient@example.com",
        completed_campaign,
        "/tmp/results.docx"
    )
    
    sent_message = mock_server.send_message.call_args[0][0]
    message_str = str(sent_message)
    
    assert "5000" in message_str


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_email_with_missing_completed_date(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test email content when completed_at is None"""
    mock_exists.return_value = True
    completed_campaign.completed_at = None
    
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    email_service.send_campaign_results(
        "recipient@example.com",
        completed_campaign,
        "/tmp/results.docx"
    )
    
    sent_message = mock_server.send_message.call_args[0][0]
    message_str = str(sent_message)
    
    # Should handle missing date gracefully
    assert "N/A" in message_str or "not available" in message_str.lower()


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_email_html_formatting(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test that email uses HTML formatting"""
    mock_exists.return_value = True
    
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    email_service.send_campaign_results(
        "recipient@example.com",
        completed_campaign,
        "/tmp/results.docx"
    )
    
    sent_message = mock_server.send_message.call_args[0][0]
    message_str = str(sent_message)
    
    # Verify HTML content
    assert "text/html" in message_str or "<html>" in message_str
    assert "<body>" in message_str or "text/html" in message_str


# ─── Test SMTP Configuration ─────────────────────────────────────────────────


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_uses_correct_smtp_server(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test that correct SMTP server and port are used"""
    mock_exists.return_value = True
    
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    email_service.send_campaign_results(
        "recipient@example.com",
        completed_campaign,
        "/tmp/results.docx"
    )
    
    # Verify Gmail SMTP server and port
    mock_smtp.assert_called_once_with("smtp.gmail.com", 587)


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_uses_tls_encryption(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test that TLS encryption is used"""
    mock_exists.return_value = True
    
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    email_service.send_campaign_results(
        "recipient@example.com",
        completed_campaign,
        "/tmp/results.docx"
    )
    
    # Verify STARTTLS was called before login
    mock_server.starttls.assert_called_once()
    
    # Verify login was called after STARTTLS
    call_order = [call[0] for call in mock_server.method_calls]
    starttls_index = call_order.index('starttls')
    login_index = call_order.index('login')
    assert starttls_index < login_index


# ─── Test Multiple Recipients ────────────────────────────────────────────────


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_send_to_multiple_recipients(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test sending emails to multiple recipients"""
    mock_exists.return_value = True
    
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
    
    for recipient in recipients:
        email_service.send_campaign_results(
            recipient,
            completed_campaign,
            "/tmp/results.docx"
        )
    
    # Verify email was sent 3 times
    assert mock_server.send_message.call_count == 3


# ─── Test Connection Management ──────────────────────────────────────────────


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_smtp_connection_cleanup(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test that SMTP connection is properly closed"""
    mock_exists.return_value = True
    
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    mock_smtp.return_value.__exit__ = MagicMock()
    
    email_service.send_campaign_results(
        "recipient@example.com",
        completed_campaign,
        "/tmp/results.docx"
    )
    
    # Verify context manager was used (connection auto-closed)
    mock_smtp.return_value.__exit__.assert_called_once()


@patch('smtplib.SMTP')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_smtp_connection_error_cleanup(
    mock_exists,
    mock_file,
    mock_smtp,
    email_service,
    completed_campaign
):
    """Test that connection is cleaned up even on error"""
    mock_exists.return_value = True
    
    mock_server = MagicMock()
    mock_server.send_message.side_effect = smtplib.SMTPException("Send failed")
    mock_smtp.return_value.__enter__.return_value = mock_server
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
    
    try:
        email_service.send_campaign_results(
            "recipient@example.com",
            completed_campaign,
            "/tmp/results.docx"
        )
        # Should have raised RuntimeError
        assert False, "Expected RuntimeError to be raised"
    except RuntimeError:
        pass  # Expected
    
    # Verify connection was still closed
    mock_smtp.return_value.__exit__.assert_called_once()
