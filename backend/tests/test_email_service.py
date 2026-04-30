"""
Unit Tests for EmailService

Tests the email creation and sending functionality.
"""

import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw==")

from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock, mock_open
from email.mime.multipart import MIMEMultipart
from uuid import uuid4
import smtplib
import pytest

from src.models.campaign import Campaign, CampaignStatus, CampaignConfig, SearchType
from src.services.email_service import EmailService


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def email_service():
    """Create an EmailService instance"""
    return EmailService(sender_email="sender@example.com", smtp_password="test_password")


@pytest.fixture
def sample_campaign():
    """Create a sample campaign"""
    config = CampaignConfig(
        profiles=["elonmusk"],
        keywords=[],
        language="en",
        min_likes=10,
        min_retweets=5,
        min_replies=2,
        hours_back=24,
    )

    return Campaign(
        id=uuid4(),
        name="Test Campaign",
        social_network="twitter",
        search_type="profile",
        status=CampaignStatus.COMPLETED,
        config=config,
        results_count=50,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
        completed_at=datetime.now(tz=timezone.utc),
    )


# ─── Test create_message ─────────────────────────────────────────────────────


def test_create_message_returns_mime_multipart(email_service, sample_campaign):
    """Test that create_message returns a MIMEMultipart object"""
    msg = email_service.create_message("recipient@example.com", sample_campaign)

    assert isinstance(msg, MIMEMultipart)


def test_create_message_sets_from_address(email_service, sample_campaign):
    """Test that create_message sets the From address"""
    msg = email_service.create_message("recipient@example.com", sample_campaign)

    assert msg["From"] == "sender@example.com"


def test_create_message_sets_to_address(email_service, sample_campaign):
    """Test that create_message sets the To address"""
    msg = email_service.create_message("recipient@example.com", sample_campaign)

    assert msg["To"] == "recipient@example.com"


def test_create_message_sets_subject_with_campaign_name(email_service, sample_campaign):
    """Test that create_message sets subject with campaign name"""
    msg = email_service.create_message("recipient@example.com", sample_campaign)

    assert "Test Campaign" in msg["Subject"]
    assert "Campaign Results" in msg["Subject"]


def test_create_message_includes_campaign_name_in_body(email_service, sample_campaign):
    """Test that create_message includes campaign name in body"""
    msg = email_service.create_message("recipient@example.com", sample_campaign)

    # Get the HTML body
    body = str(msg)
    assert "Test Campaign" in body


def test_create_message_includes_campaign_status_in_body(email_service, sample_campaign):
    """Test that create_message includes campaign status in body"""
    msg = email_service.create_message("recipient@example.com", sample_campaign)

    body = str(msg)
    assert "COMPLETED" in body or "completed" in body


def test_create_message_includes_results_count_in_body(email_service, sample_campaign):
    """Test that create_message includes results count in body"""
    msg = email_service.create_message("recipient@example.com", sample_campaign)

    body = str(msg)
    assert "50" in body  # results_count


def test_create_message_includes_completed_date_when_available(email_service, sample_campaign):
    """Test that create_message includes completed date when available"""
    msg = email_service.create_message("recipient@example.com", sample_campaign)

    body = str(msg)
    # Should include some date format
    assert any(char.isdigit() for char in body)


def test_create_message_handles_missing_completed_date(email_service, sample_campaign):
    """Test that create_message handles missing completed date"""
    sample_campaign.completed_at = None

    msg = email_service.create_message("recipient@example.com", sample_campaign)

    body = str(msg)
    assert "N/A" in body or "not available" in body.lower()


def test_create_message_creates_html_body(email_service, sample_campaign):
    """Test that create_message creates HTML body"""
    msg = email_service.create_message("recipient@example.com", sample_campaign)

    body = str(msg)
    assert "<html>" in body or "text/html" in body


# ─── Test _attach_document ───────────────────────────────────────────────────


@patch("builtins.open", new_callable=mock_open, read_data=b"fake docx content")
@patch("os.path.exists")
def test_attach_document_attaches_file(mock_exists, mock_file, email_service, sample_campaign):
    """Test that _attach_document attaches a file"""
    mock_exists.return_value = True

    msg = email_service.create_message("recipient@example.com", sample_campaign)
    email_service._attach_document(msg, "/tmp/test.docx")

    # Check that file was opened
    mock_file.assert_called_once_with("/tmp/test.docx", "rb")

    # Check that message has attachments
    assert len(msg.get_payload()) > 1  # More than just the body


@patch("os.path.exists")
def test_attach_document_handles_missing_file(mock_exists, email_service, sample_campaign):
    """Test that _attach_document handles missing file gracefully"""
    mock_exists.return_value = False

    msg = email_service.create_message("recipient@example.com", sample_campaign)

    # Should not raise an error
    email_service._attach_document(msg, "/tmp/nonexistent.docx")


@patch("builtins.open", new_callable=mock_open, read_data=b"fake docx content")
@patch("os.path.exists")
def test_attach_document_uses_correct_filename(
    mock_exists, mock_file, email_service, sample_campaign
):
    """Test that _attach_document uses correct filename in attachment"""
    mock_exists.return_value = True

    msg = email_service.create_message("recipient@example.com", sample_campaign)
    email_service._attach_document(msg, "/tmp/path/to/results.docx")

    # Check that attachment has correct filename
    body = str(msg)
    assert "results.docx" in body


# ─── Test send_campaign_results ──────────────────────────────────────────────


@patch("smtplib.SMTP")
@patch("builtins.open", new_callable=mock_open, read_data=b"fake docx content")
@patch("os.path.exists")
def test_send_campaign_results_sends_email(
    mock_exists, mock_file, mock_smtp, email_service, sample_campaign
):
    """Test that send_campaign_results sends email successfully"""
    mock_exists.return_value = True
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    email_service.send_campaign_results("recipient@example.com", sample_campaign, "/tmp/test.docx")

    # Verify SMTP connection was made
    mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("sender@example.com", "test_password")
    mock_server.send_message.assert_called_once()


@patch("smtplib.SMTP")
@patch("builtins.open", new_callable=mock_open, read_data=b"fake docx content")
@patch("os.path.exists")
def test_send_campaign_results_raises_error_on_auth_failure(
    mock_exists, mock_file, mock_smtp, email_service, sample_campaign
):
    """Test that send_campaign_results raises error on authentication failure"""
    mock_exists.return_value = True
    mock_server = MagicMock()
    mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
    mock_smtp.return_value.__enter__.return_value = mock_server

    with pytest.raises(RuntimeError) as exc_info:
        email_service.send_campaign_results(
            "recipient@example.com", sample_campaign, "/tmp/test.docx"
        )

    assert "authentication" in str(exc_info.value).lower()


@patch("smtplib.SMTP")
@patch("builtins.open", new_callable=mock_open, read_data=b"fake docx content")
@patch("os.path.exists")
def test_send_campaign_results_raises_error_on_smtp_failure(
    mock_exists, mock_file, mock_smtp, email_service, sample_campaign
):
    """Test that send_campaign_results raises error on SMTP failure"""
    mock_exists.return_value = True
    mock_server = MagicMock()
    mock_server.send_message.side_effect = smtplib.SMTPException("SMTP error")
    mock_smtp.return_value.__enter__.return_value = mock_server

    with pytest.raises(RuntimeError) as exc_info:
        email_service.send_campaign_results(
            "recipient@example.com", sample_campaign, "/tmp/test.docx"
        )

    assert "failed to send" in str(exc_info.value).lower()


@patch("smtplib.SMTP")
@patch("builtins.open", new_callable=mock_open, read_data=b"fake docx content")
@patch("os.path.exists")
def test_send_campaign_results_uses_starttls(
    mock_exists, mock_file, mock_smtp, email_service, sample_campaign
):
    """Test that send_campaign_results uses STARTTLS for security"""
    mock_exists.return_value = True
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    email_service.send_campaign_results("recipient@example.com", sample_campaign, "/tmp/test.docx")

    # Verify STARTTLS was called
    mock_server.starttls.assert_called_once()


# ─── Test initialization ─────────────────────────────────────────────────────


def test_email_service_initialization():
    """Test that EmailService initializes correctly"""
    service = EmailService(sender_email="test@example.com", smtp_password="password123")

    assert service._sender == "test@example.com"
    assert service._password == "password123"


def test_email_service_stores_credentials():
    """Test that EmailService stores credentials correctly"""
    service = EmailService(sender_email="sender@gmail.com", smtp_password="app_password")

    assert service._sender == "sender@gmail.com"
    assert service._password == "app_password"
