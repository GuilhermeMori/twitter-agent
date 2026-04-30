"""
Unit Tests for StorageService

Tests the file upload, download, and deletion functionality.
"""

import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw==")

from unittest.mock import Mock, MagicMock, patch, mock_open
import pytest

from src.services.storage_service import StorageService


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client"""
    return Mock()


@pytest.fixture
def storage_service(mock_supabase_client):
    """Create a StorageService with mocked Supabase client"""
    return StorageService(mock_supabase_client)


# ─── Test upload_document ────────────────────────────────────────────────────


@patch("builtins.open", new_callable=mock_open, read_data=b"fake docx content")
@patch("os.path.exists")
def test_upload_document_uploads_file(
    mock_exists, mock_file, storage_service, mock_supabase_client
):
    """Test that upload_document uploads file successfully"""
    mock_exists.return_value = True
    mock_storage = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_storage
    mock_storage.get_public_url.return_value = "https://storage.example.com/file.docx"

    url = storage_service.upload_document("campaign-123", "/tmp/test.docx")

    assert url == "https://storage.example.com/file.docx"
    # from_ is called once for upload and once for get_public_url
    assert mock_supabase_client.storage.from_.call_count >= 1
    mock_storage.upload.assert_called_once()


@patch("builtins.open", new_callable=mock_open, read_data=b"fake docx content")
@patch("os.path.exists")
def test_upload_document_uses_correct_storage_path(
    mock_exists, mock_file, storage_service, mock_supabase_client
):
    """Test that upload_document uses correct storage path"""
    mock_exists.return_value = True
    mock_storage = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_storage
    mock_storage.get_public_url.return_value = "https://storage.example.com/file.docx"

    storage_service.upload_document("campaign-123", "/tmp/test.docx")

    # Verify correct storage path
    call_args = mock_storage.upload.call_args
    assert call_args[1]["path"] == "campaigns/campaign-123/results.docx"


@patch("builtins.open", new_callable=mock_open, read_data=b"fake docx content")
@patch("os.path.exists")
def test_upload_document_sets_correct_content_type(
    mock_exists, mock_file, storage_service, mock_supabase_client
):
    """Test that upload_document sets correct content type"""
    mock_exists.return_value = True
    mock_storage = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_storage
    mock_storage.get_public_url.return_value = "https://storage.example.com/file.docx"

    storage_service.upload_document("campaign-123", "/tmp/test.docx")

    # Verify content type
    call_args = mock_storage.upload.call_args
    assert "file_options" in call_args[1]
    assert "content-type" in call_args[1]["file_options"]
    assert "wordprocessingml" in call_args[1]["file_options"]["content-type"]


@patch("os.path.exists")
def test_upload_document_raises_error_on_missing_file(mock_exists, storage_service):
    """Test that upload_document raises error when file doesn't exist"""
    mock_exists.return_value = False

    with pytest.raises(FileNotFoundError):
        storage_service.upload_document("campaign-123", "/tmp/nonexistent.docx")


@patch("builtins.open", new_callable=mock_open, read_data=b"fake docx content")
@patch("os.path.exists")
def test_upload_document_raises_error_on_upload_failure(
    mock_exists, mock_file, storage_service, mock_supabase_client
):
    """Test that upload_document raises error on upload failure"""
    mock_exists.return_value = True
    mock_storage = MagicMock()
    mock_storage.upload.side_effect = Exception("Upload failed")
    mock_supabase_client.storage.from_.return_value = mock_storage

    with pytest.raises(RuntimeError) as exc_info:
        storage_service.upload_document("campaign-123", "/tmp/test.docx")

    assert "upload failed" in str(exc_info.value).lower()


@patch("builtins.open", new_callable=mock_open, read_data=b"fake docx content")
@patch("os.path.exists")
def test_upload_document_opens_file_in_binary_mode(
    mock_exists, mock_file, storage_service, mock_supabase_client
):
    """Test that upload_document opens file in binary mode"""
    mock_exists.return_value = True
    mock_storage = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_storage
    mock_storage.get_public_url.return_value = "https://storage.example.com/file.docx"

    storage_service.upload_document("campaign-123", "/tmp/test.docx")

    # Verify file was opened in binary mode
    mock_file.assert_called_once_with("/tmp/test.docx", "rb")


# ─── Test get_signed_url ─────────────────────────────────────────────────────


def test_get_signed_url_returns_url(storage_service, mock_supabase_client):
    """Test that get_signed_url returns a signed URL"""
    mock_storage = MagicMock()
    mock_storage.create_signed_url.return_value = {"signedURL": "https://signed.url/file.docx"}
    mock_supabase_client.storage.from_.return_value = mock_storage

    url = storage_service.get_signed_url("campaign-123")

    assert url == "https://signed.url/file.docx"


def test_get_signed_url_uses_correct_storage_path(storage_service, mock_supabase_client):
    """Test that get_signed_url uses correct storage path"""
    mock_storage = MagicMock()
    mock_storage.create_signed_url.return_value = {"signedURL": "https://signed.url/file.docx"}
    mock_supabase_client.storage.from_.return_value = mock_storage

    storage_service.get_signed_url("campaign-123")

    # Verify correct storage path
    call_args = mock_storage.create_signed_url.call_args
    assert call_args[1]["path"] == "campaigns/campaign-123/results.docx"


def test_get_signed_url_uses_default_expiry(storage_service, mock_supabase_client):
    """Test that get_signed_url uses default expiry time"""
    mock_storage = MagicMock()
    mock_storage.create_signed_url.return_value = {"signedURL": "https://signed.url/file.docx"}
    mock_supabase_client.storage.from_.return_value = mock_storage

    storage_service.get_signed_url("campaign-123")

    # Verify default expiry (3600 seconds = 1 hour)
    call_args = mock_storage.create_signed_url.call_args
    assert call_args[1]["expires_in"] == 3600


def test_get_signed_url_accepts_custom_expiry(storage_service, mock_supabase_client):
    """Test that get_signed_url accepts custom expiry time"""
    mock_storage = MagicMock()
    mock_storage.create_signed_url.return_value = {"signedURL": "https://signed.url/file.docx"}
    mock_supabase_client.storage.from_.return_value = mock_storage

    storage_service.get_signed_url("campaign-123", expires_in=7200)

    # Verify custom expiry
    call_args = mock_storage.create_signed_url.call_args
    assert call_args[1]["expires_in"] == 7200


def test_get_signed_url_handles_alternative_response_key(storage_service, mock_supabase_client):
    """Test that get_signed_url handles alternative response key (signedUrl)"""
    mock_storage = MagicMock()
    mock_storage.create_signed_url.return_value = {"signedUrl": "https://signed.url/file.docx"}
    mock_supabase_client.storage.from_.return_value = mock_storage

    url = storage_service.get_signed_url("campaign-123")

    assert url == "https://signed.url/file.docx"


def test_get_signed_url_raises_error_on_missing_url(storage_service, mock_supabase_client):
    """Test that get_signed_url raises error when URL is missing"""
    mock_storage = MagicMock()
    mock_storage.create_signed_url.return_value = {}  # No URL in response
    mock_supabase_client.storage.from_.return_value = mock_storage

    with pytest.raises(RuntimeError) as exc_info:
        storage_service.get_signed_url("campaign-123")

    assert "signed url" in str(exc_info.value).lower()


def test_get_signed_url_raises_error_on_failure(storage_service, mock_supabase_client):
    """Test that get_signed_url raises error on failure"""
    mock_storage = MagicMock()
    mock_storage.create_signed_url.side_effect = Exception("Failed to create signed URL")
    mock_supabase_client.storage.from_.return_value = mock_storage

    with pytest.raises(RuntimeError) as exc_info:
        storage_service.get_signed_url("campaign-123")

    assert "failed to generate" in str(exc_info.value).lower()


# ─── Test delete_document ────────────────────────────────────────────────────


def test_delete_document_deletes_file(storage_service, mock_supabase_client):
    """Test that delete_document deletes file successfully"""
    mock_storage = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_storage

    storage_service.delete_document("campaign-123")

    mock_supabase_client.storage.from_.assert_called_once_with("campaign-documents")
    mock_storage.remove.assert_called_once()


def test_delete_document_uses_correct_storage_path(storage_service, mock_supabase_client):
    """Test that delete_document uses correct storage path"""
    mock_storage = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_storage

    storage_service.delete_document("campaign-123")

    # Verify correct storage path
    call_args = mock_storage.remove.call_args
    assert "campaigns/campaign-123/results.docx" in call_args[0][0]


def test_delete_document_handles_missing_file_gracefully(storage_service, mock_supabase_client):
    """Test that delete_document handles missing file gracefully"""
    mock_storage = MagicMock()
    mock_storage.remove.side_effect = Exception("File not found")
    mock_supabase_client.storage.from_.return_value = mock_storage

    # Should not raise an error
    storage_service.delete_document("campaign-123")


def test_delete_document_handles_deletion_failure_gracefully(storage_service, mock_supabase_client):
    """Test that delete_document handles deletion failure gracefully"""
    mock_storage = MagicMock()
    mock_storage.remove.side_effect = Exception("Deletion failed")
    mock_supabase_client.storage.from_.return_value = mock_storage

    # Should not raise an error (just logs warning)
    storage_service.delete_document("campaign-123")


# ─── Test initialization ─────────────────────────────────────────────────────


def test_storage_service_initialization(mock_supabase_client):
    """Test that StorageService initializes correctly"""
    service = StorageService(mock_supabase_client)

    assert service._client == mock_supabase_client


def test_storage_service_stores_client_reference(mock_supabase_client):
    """Test that StorageService stores client reference"""
    service = StorageService(mock_supabase_client)

    assert service._client is mock_supabase_client
