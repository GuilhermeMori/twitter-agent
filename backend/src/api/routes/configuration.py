"""Configuration API routes"""

from fastapi import APIRouter, Depends, status
from supabase import Client

from src.core.database import get_db
from src.models.configuration import ConfigurationDTO, ConfigurationResponseDTO
from src.repositories.configuration_repository import ConfigurationRepository
from src.services.configuration_manager import ConfigurationManager
from src.utils.encryption import Encryptor
from src.core.logging_config import get_logger

logger = get_logger("api.routes.configuration")

router = APIRouter()


# ─── Dependency injection helpers ────────────────────────────────────────────

def get_configuration_manager(db: Client = Depends(get_db)) -> ConfigurationManager:
    """DI: ConfigurationManager with all dependencies."""
    repo = ConfigurationRepository(db)
    encryptor = Encryptor()
    return ConfigurationManager(repo, encryptor)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get(
    "/configuration",
    response_model=ConfigurationResponseDTO,
    summary="Get user configuration",
    description="Retrieve the stored configuration with masked tokens.",
)
async def get_configuration(
    mgr: ConfigurationManager = Depends(get_configuration_manager),
) -> ConfigurationResponseDTO:
    """
    GET /api/configuration

    Returns the user's configuration with all tokens masked for security.
    Raises HTTP 400 if no configuration has been saved yet.
    """
    config = mgr.get_configuration()
    masked = mgr.mask_tokens(config)
    logger.info("Configuration retrieved (masked)")
    return masked


@router.post(
    "/configuration",
    status_code=status.HTTP_201_CREATED,
    summary="Save user configuration",
    description="Store API tokens and SMTP credentials (encrypted).",
)
async def save_configuration(
    config: ConfigurationDTO,
    mgr: ConfigurationManager = Depends(get_configuration_manager),
) -> dict:
    """
    POST /api/configuration

    Encrypts and stores the user's API tokens and SMTP password.
    If a configuration already exists, it is updated.
    """
    # Basic validation
    if not mgr.validate_tokens(config):
        logger.warning("Invalid configuration submitted")
        return {"success": False, "message": "Invalid token format"}

    mgr.save_configuration(config)
    logger.info("Configuration saved for %s", config.user_email)
    return {"success": True, "message": "Configuration saved successfully"}
