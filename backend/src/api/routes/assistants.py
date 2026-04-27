"""Assistants API routes"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from supabase import Client

from src.core.database import get_db
from src.models.assistant import (
    Assistant,
    AssistantUpdateDTO,
)
from src.repositories.assistant_repository import AssistantRepository
from src.services.assistant_service import AssistantService
from src.core.logging_config import get_logger

logger = get_logger("api.routes.assistants")

router = APIRouter()


# ─── Dependency injection helpers ────────────────────────────────────────────

def get_assistant_service(db: Client = Depends(get_db)) -> AssistantService:
    """DI: AssistantService with all dependencies."""
    repo = AssistantRepository(db)
    return AssistantService(repo)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get(
    "/assistants",
    summary="Listar assistentes",
    description="Retorna os 3 assistentes fixos do sistema (Beto, Cadu, Rita).",
)
async def list_assistants(
    service: AssistantService = Depends(get_assistant_service),
) -> dict:
    """
    GET /api/assistants

    Returns the 3 fixed assistants ordered by role.
    """
    assistants = service.list_assistants()
    logger.info("Listed %d assistants", len(assistants))
    return {
        "items": assistants,
        "total": len(assistants),
        "page": 1,
        "limit": 20,
        "total_pages": 1,
    }


@router.get(
    "/assistants/{assistant_id}",
    response_model=Assistant,
    summary="Detalhes do assistente",
    description="Retorna os detalhes completos de um assistente específico.",
)
async def get_assistant(
    assistant_id: str,
    service: AssistantService = Depends(get_assistant_service),
) -> Assistant:
    """
    GET /api/assistants/{id}

    Returns the complete assistant record.
    Raises HTTP 404 if the assistant does not exist.
    """
    assistant = service.get_assistant(assistant_id)
    logger.info("Retrieved assistant: %s", assistant_id)
    return assistant


@router.put(
    "/assistants/{assistant_id}",
    response_model=Assistant,
    summary="Atualizar assistente",
    description="Atualiza as instruções e configurações de um assistente.",
)
async def update_assistant(
    assistant_id: str,
    data: AssistantUpdateDTO,
    service: AssistantService = Depends(get_assistant_service),
) -> Assistant:
    """
    PUT /api/assistants/{id}

    Updates the specified assistant with new data.
    Only provided fields will be updated.

    Raises HTTP 404 if the assistant does not exist.
    Raises HTTP 400 if no fields are provided for update.
    """
    assistant = service.update_assistant(assistant_id, data)
    logger.info("Updated assistant: %s", assistant_id)
    return assistant


@router.post(
    "/assistants",
    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
    summary="Criar assistente (bloqueado)",
    description="Criar novos assistentes não é permitido. O sistema possui exatamente 3 assistentes fixos.",
)
async def create_assistant() -> JSONResponse:
    """
    POST /api/assistants

    Always returns 405 - creating assistants is not allowed.
    """
    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content={
            "detail": "Criar novos assistentes não é permitido. O sistema possui exatamente 3 assistentes fixos."
        },
    )


@router.delete(
    "/assistants/{assistant_id}",
    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
    summary="Excluir assistente (bloqueado)",
    description="Excluir assistentes não é permitido. O sistema requer exatamente 3 assistentes fixos.",
)
async def delete_assistant(assistant_id: str) -> JSONResponse:
    """
    DELETE /api/assistants/{id}

    Always returns 405 - deleting assistants is not allowed.
    """
    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content={
            "detail": "Excluir assistentes não é permitido. O sistema requer exatamente 3 assistentes fixos."
        },
    )
