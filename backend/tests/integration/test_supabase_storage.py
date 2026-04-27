"""
Integration Tests for Supabase Storage Operations

Tests file upload, download, signed URL generation, and deletion.
Uses realistic mocked Supabase Storage responses.
"""

import os
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw==")

from unittest.mock import Mock, MagicMock, patch, mock_open
from uuid import uuid4
import pytest

from src.services.storage_service import StorageService


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    return Mock()


@pytest.fixture
def storage_service(mock_supabase_client):
    """Storage service with mocked client"""
    return StorageService(mock_supabase_client)


@pytest.fixture
def campaign_id():
    """Sample campaign ID"""
    return str(uuid4())


@pytest.fixture
def realistic_document_content():
    """Realistic .docx file content (binary)"""
    # Minimal .docx file structure (ZIP format)
    return b'PK\x03\x04' + b'\x00' * 100  # Simplified docx header


# ─── Test Complete Upload Workflow ───────────────────────────────────────────


@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_complete_upload_workflow(
    mock_exists,
    mock_file,
    storage_service,
    mock_supabase_client,
    campaign_id
):
    """Test complete document upload workflow"""
    mock_exists.return_value = True
    
    # Mock storage chain
    mock_storage = MagicMock()
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    
    # Mock successful upload
    mock_bucket.upload.return_value = {
        "Key": f"campaigns/{campaign_id}/results.docx",
        "id": str(uuid4())
    }
    
    # Mock public URL generation
    expected_url = f"https://test.supabase.co/storage/v1/object/public/campaign-documents/campaigns/{campaign_id}/results.docx"
    mock_bucket.get_public_url.return_value = expected_url
    
    # Execute upload
    document_url = storage_service.upload_document(campaign_id, "/tmp/test.docx")
    
    # Verify file was opened in binary mode
    mock_file.assert_called_once_with("/tmp/test.docx", "rb")
    
    # Verify storage bucket was accessed
    mock_supabase_client.storage.from_.assert_called_with("campaign-documents")
    
    # Verify upload was called with correct parameters
    upload_call = mock_bucket.upload.call_args
    assert upload_call[1]["path"] == f"campaigns/{campaign_id}/results.docx"
    assert "file_options" in upload_call[1]
    assert "content-type" in upload_call[1]["file_options"]
    assert "wordprocessingml" in upload_call[1]["file_options"]["content-type"]
    
    # Verify public URL was generated
    mock_bucket.get_public_url.assert_called_once_with(f"campaigns/{campaign_id}/results.docx")
    
    # Verify result
    assert document_url == expected_url


@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_upload_with_folder_structure(
    mock_exists,
    mock_file,
    storage_service,
    mock_supabase_client,
    campaign_id
):
    """Test that upload creates proper folder structure"""
    mock_exists.return_value = True
    
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    mock_bucket.get_public_url.return_value = "https://storage.example.com/file.docx"
    
    storage_service.upload_document(campaign_id, "/tmp/test.docx")
    
    # Verify folder structure: campaigns/{campaign_id}/results.docx
    upload_path = mock_bucket.upload.call_args[1]["path"]
    assert upload_path.startswith("campaigns/")
    assert campaign_id in upload_path
    assert upload_path.endswith("/results.docx")


# ─── Test Signed URL Generation ──────────────────────────────────────────────


def test_generate_signed_url(storage_service, mock_supabase_client, campaign_id):
    """Test generating signed URL for document download"""
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    
    expected_signed_url = f"https://test.supabase.co/storage/v1/object/sign/campaign-documents/campaigns/{campaign_id}/results.docx?token=abc123"
    mock_bucket.create_signed_url.return_value = {
        "signedURL": expected_signed_url
    }
    
    signed_url = storage_service.get_signed_url(campaign_id)
    
    # Verify storage bucket was accessed
    mock_supabase_client.storage.from_.assert_called_once_with("campaign-documents")
    
    # Verify signed URL was created with correct parameters
    create_call = mock_bucket.create_signed_url.call_args
    assert create_call[1]["path"] == f"campaigns/{campaign_id}/results.docx"
    assert create_call[1]["expires_in"] == 3600  # Default 1 hour
    
    # Verify result
    assert signed_url == expected_signed_url


def test_generate_signed_url_with_custom_expiry(storage_service, mock_supabase_client, campaign_id):
    """Test generating signed URL with custom expiry time"""
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    
    mock_bucket.create_signed_url.return_value = {
        "signedURL": "https://storage.example.com/signed"
    }
    
    storage_service.get_signed_url(campaign_id, expires_in=7200)
    
    # Verify custom expiry was used
    create_call = mock_bucket.create_signed_url.call_args
    assert create_call[1]["expires_in"] == 7200


def test_generate_signed_url_alternative_response_format(storage_service, mock_supabase_client, campaign_id):
    """Test handling alternative response format (signedUrl vs signedURL)"""
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    
    # Alternative key name
    expected_url = "https://storage.example.com/signed"
    mock_bucket.create_signed_url.return_value = {
        "signedUrl": expected_url  # lowercase 'url'
    }
    
    signed_url = storage_service.get_signed_url(campaign_id)
    
    assert signed_url == expected_url


# ─── Test File Deletion ──────────────────────────────────────────────────────


def test_delete_document(storage_service, mock_supabase_client, campaign_id):
    """Test deleting a document from storage"""
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    
    storage_service.delete_document(campaign_id)
    
    # Verify storage bucket was accessed
    mock_supabase_client.storage.from_.assert_called_once_with("campaign-documents")
    
    # Verify remove was called with correct path
    remove_call = mock_bucket.remove.call_args
    assert f"campaigns/{campaign_id}/results.docx" in remove_call[0][0]


def test_delete_document_handles_missing_file(storage_service, mock_supabase_client, campaign_id):
    """Test that delete handles missing files gracefully"""
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    mock_bucket.remove.side_effect = Exception("File not found")
    
    # Should not raise an error
    storage_service.delete_document(campaign_id)


def test_delete_document_handles_permission_error(storage_service, mock_supabase_client, campaign_id):
    """Test that delete handles permission errors gracefully"""
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    mock_bucket.remove.side_effect = Exception("Permission denied")
    
    # Should not raise an error (just logs warning)
    storage_service.delete_document(campaign_id)


# ─── Test Error Scenarios ────────────────────────────────────────────────────


@patch('os.path.exists')
def test_upload_missing_file_error(mock_exists, storage_service, campaign_id):
    """Test upload fails when file doesn't exist"""
    mock_exists.return_value = False
    
    with pytest.raises(FileNotFoundError) as exc_info:
        storage_service.upload_document(campaign_id, "/tmp/nonexistent.docx")
    
    assert "not found" in str(exc_info.value).lower()


@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_upload_storage_quota_exceeded(mock_exists, mock_file, storage_service, mock_supabase_client, campaign_id):
    """Test handling of storage quota exceeded error"""
    mock_exists.return_value = True
    
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    mock_bucket.upload.side_effect = Exception("Storage quota exceeded")
    
    with pytest.raises(RuntimeError) as exc_info:
        storage_service.upload_document(campaign_id, "/tmp/test.docx")
    
    assert "upload failed" in str(exc_info.value).lower()


@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_upload_network_error(mock_exists, mock_file, storage_service, mock_supabase_client, campaign_id):
    """Test handling of network errors during upload"""
    mock_exists.return_value = True
    
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    mock_bucket.upload.side_effect = Exception("Network timeout")
    
    with pytest.raises(RuntimeError):
        storage_service.upload_document(campaign_id, "/tmp/test.docx")


def test_signed_url_missing_file_error(storage_service, mock_supabase_client, campaign_id):
    """Test signed URL generation fails for missing file"""
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    mock_bucket.create_signed_url.side_effect = Exception("File not found")
    
    with pytest.raises(RuntimeError) as exc_info:
        storage_service.get_signed_url(campaign_id)
    
    assert "failed to generate" in str(exc_info.value).lower()


def test_signed_url_missing_in_response(storage_service, mock_supabase_client, campaign_id):
    """Test handling of missing signed URL in response"""
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    mock_bucket.create_signed_url.return_value = {}  # No URL in response
    
    with pytest.raises(RuntimeError) as exc_info:
        storage_service.get_signed_url(campaign_id)
    
    assert "did not return" in str(exc_info.value).lower()


@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_upload_invalid_file_type(mock_exists, mock_file, storage_service, mock_supabase_client, campaign_id):
    """Test upload with invalid file type"""
    mock_exists.return_value = True
    
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    mock_bucket.upload.side_effect = Exception("Invalid file type")
    
    with pytest.raises(RuntimeError):
        storage_service.upload_document(campaign_id, "/tmp/test.txt")


# ─── Test Content Type Handling ──────────────────────────────────────────────


@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_upload_sets_correct_content_type(mock_exists, mock_file, storage_service, mock_supabase_client, campaign_id):
    """Test that upload sets correct MIME type for .docx files"""
    mock_exists.return_value = True
    
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    mock_bucket.get_public_url.return_value = "https://storage.example.com/file.docx"
    
    storage_service.upload_document(campaign_id, "/tmp/test.docx")
    
    # Verify content type
    upload_call = mock_bucket.upload.call_args
    file_options = upload_call[1]["file_options"]
    content_type = file_options["content-type"]
    
    assert content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


# ─── Test Public URL Generation ──────────────────────────────────────────────


@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_upload_returns_public_url(mock_exists, mock_file, storage_service, mock_supabase_client, campaign_id):
    """Test that upload returns public URL"""
    mock_exists.return_value = True
    
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    
    expected_url = f"https://test.supabase.co/storage/v1/object/public/campaign-documents/campaigns/{campaign_id}/results.docx"
    mock_bucket.get_public_url.return_value = expected_url
    
    url = storage_service.upload_document(campaign_id, "/tmp/test.docx")
    
    assert url == expected_url
    assert "campaign-documents" in url
    assert campaign_id in url


# ─── Test Multiple Operations Workflow ───────────────────────────────────────


@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_upload_then_generate_signed_url(
    mock_exists,
    mock_file,
    storage_service,
    mock_supabase_client,
    campaign_id
):
    """Test uploading a document then generating a signed URL"""
    mock_exists.return_value = True
    
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    
    # Mock upload
    public_url = f"https://storage.example.com/campaigns/{campaign_id}/results.docx"
    mock_bucket.get_public_url.return_value = public_url
    
    # Mock signed URL
    signed_url = f"{public_url}?token=abc123"
    mock_bucket.create_signed_url.return_value = {"signedURL": signed_url}
    
    # Upload document
    upload_url = storage_service.upload_document(campaign_id, "/tmp/test.docx")
    assert upload_url == public_url
    
    # Generate signed URL
    download_url = storage_service.get_signed_url(campaign_id)
    assert download_url == signed_url


@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_upload_then_delete(
    mock_exists,
    mock_file,
    storage_service,
    mock_supabase_client,
    campaign_id
):
    """Test uploading a document then deleting it"""
    mock_exists.return_value = True
    
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    mock_bucket.get_public_url.return_value = "https://storage.example.com/file.docx"
    
    # Upload document
    storage_service.upload_document(campaign_id, "/tmp/test.docx")
    
    # Delete document
    storage_service.delete_document(campaign_id)
    
    # Verify both operations used same bucket
    assert mock_supabase_client.storage.from_.call_count >= 2
    
    # Verify delete was called
    mock_bucket.remove.assert_called_once()


# ─── Test Bucket Configuration ───────────────────────────────────────────────


def test_uses_correct_bucket_name(storage_service, mock_supabase_client, campaign_id):
    """Test that all operations use the correct bucket name"""
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    mock_bucket.create_signed_url.return_value = {"signedURL": "https://test.url"}
    
    storage_service.get_signed_url(campaign_id)
    
    # Verify correct bucket name
    mock_supabase_client.storage.from_.assert_called_with("campaign-documents")


@patch('builtins.open', new_callable=mock_open, read_data=b'fake docx content')
@patch('os.path.exists')
def test_consistent_path_structure(mock_exists, mock_file, storage_service, mock_supabase_client):
    """Test that path structure is consistent across operations"""
    mock_exists.return_value = True
    
    campaign_ids = [str(uuid4()) for _ in range(3)]
    
    mock_bucket = MagicMock()
    mock_supabase_client.storage.from_.return_value = mock_bucket
    mock_bucket.get_public_url.return_value = "https://storage.example.com/file.docx"
    
    for cid in campaign_ids:
        storage_service.upload_document(cid, "/tmp/test.docx")
        
        # Verify path structure
        upload_path = mock_bucket.upload.call_args[1]["path"]
        assert upload_path == f"campaigns/{cid}/results.docx"
