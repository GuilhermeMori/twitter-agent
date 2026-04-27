"""Communication Styles API routes"""

from fastapi import APIRouter, Depends, Query, status
from supabase import Client

from src.core.database import get_db
from src.models.communication_style import (
    CommunicationStyle,
    CommunicationStyleSummary,
    CommunicationStyleCreateDTO,
    CommunicationStyleUpdateDTO,
)
from src.models.campaign import PaginatedResponse
from src.repositories.communication_style_repository import CommunicationStyleRepository
from src.services.communication_style_service import CommunicationStyleService
from src.core.logging_config import get_logger

logger = get_logger("api.routes.communication_styles")

router = APIRouter()


# ─── Dependency injection helpers ────────────────────────────────────────────

def get_communication_style_service(db: Client = Depends(get_db)) -> CommunicationStyleService:
    """DI: CommunicationStyleService with all dependencies."""
    repo = CommunicationStyleRepository(db)
    return CommunicationStyleService(repo)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/communication-styles",
    status_code=status.HTTP_201_CREATED,
    summary="Criar estilo de comunicação",
    description="Cria um novo estilo de comunicação com as características especificadas.",
)
@router.post(
    "/personas",
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False
)
async def create_communication_style(
    data: CommunicationStyleCreateDTO,
    service: CommunicationStyleService = Depends(get_communication_style_service),
) -> dict:
    """
    POST /api/communication-styles or /api/personas
    """
    communication_style_id = service.create_communication_style(data)
    logger.info("Communication style created: %s", communication_style_id)
    return {"communication_style_id": communication_style_id, "message": "Estilo de comunicação criado com sucesso"}


@router.get(
    "/communication-styles",
    response_model=PaginatedResponse[CommunicationStyle],
    summary="Listar estilos de comunicação",
    description="Retorna uma lista paginada de estilos de comunicação (mais recentes primeiro).",
)
@router.get(
    "/personas",
    response_model=PaginatedResponse[CommunicationStyle],
    include_in_schema=False
)
async def list_communication_styles(
    page: int = Query(1, ge=1, description="Número da página (começa em 1)"),
    limit: int = Query(20, ge=1, le=50, description="Itens por página"),
    service: CommunicationStyleService = Depends(get_communication_style_service),
) -> PaginatedResponse[CommunicationStyle]:
    """
    GET /api/communication-styles or /api/personas
    """
    result = service.list_communication_styles(page=page, limit=limit)
    logger.info("Listed communication styles: page=%d, limit=%d, total=%d", page, limit, result.total)
    return result


@router.get(
    "/communication-styles/summaries",
    response_model=PaginatedResponse[CommunicationStyleSummary],
    summary="Listar resumos de estilos",
    description="Retorna resumos de estilos de comunicação para dropdowns e listas de seleção.",
)
@router.get(
    "/personas/summaries",
    response_model=PaginatedResponse[CommunicationStyleSummary],
    include_in_schema=False
)
async def list_communication_style_summaries(
    page: int = Query(1, ge=1, description="Número da página (começa em 1)"),
    limit: int = Query(50, ge=1, le=100, description="Itens por página"),
    service: CommunicationStyleService = Depends(get_communication_style_service),
) -> PaginatedResponse[CommunicationStyleSummary]:
    """
    GET /api/communication-styles/summaries or /api/personas/summaries
    """
    result = service.list_communication_style_summaries(page=page, limit=limit)
    logger.info("Listed communication style summaries: page=%d, limit=%d, total=%d", page, limit, result.total)
    return result


@router.get(
    "/communication-styles/default",
    response_model=CommunicationStyle,
    summary="Obter estilo padrão",
    description="Retorna o estilo de comunicação padrão. Cria um se não existir.",
)
@router.get(
    "/personas/default",
    response_model=CommunicationStyle,
    include_in_schema=False
)
async def get_default_communication_style(
    service: CommunicationStyleService = Depends(get_communication_style_service),
) -> CommunicationStyle:
    """
    GET /api/communication-styles/default or /api/personas/default
    """
    communication_style = service.get_default_communication_style()
    logger.info("Retrieved default communication style: %s", communication_style.id)
    return communication_style


@router.get(
    "/communication-styles/{style_id}",
    response_model=CommunicationStyle,
    summary="Detalhes do estilo",
    description="Retorna os detalhes completos de um estilo de comunicação específico.",
)
@router.get(
    "/personas/{style_id}",
    response_model=CommunicationStyle,
    include_in_schema=False
)
async def get_communication_style(
    style_id: str,
    service: CommunicationStyleService = Depends(get_communication_style_service),
) -> CommunicationStyle:
    """
    GET /api/communication-styles/{id} or /api/personas/{id}
    """
    communication_style = service.get_communication_style(style_id)
    logger.info("Retrieved communication style: %s", style_id)
    return communication_style


@router.put(
    "/communication-styles/{style_id}",
    response_model=CommunicationStyle,
    summary="Atualizar estilo",
    description="Atualiza as características de um estilo de comunicação existente.",
)
@router.put(
    "/personas/{style_id}",
    response_model=CommunicationStyle,
    include_in_schema=False
)
async def update_communication_style(
    style_id: str,
    data: CommunicationStyleUpdateDTO,
    service: CommunicationStyleService = Depends(get_communication_style_service),
) -> CommunicationStyle:
    """
    PUT /api/communication-styles/{id} or /api/personas/{id}
    """
    communication_style = service.update_communication_style(style_id, data)
    logger.info("Updated communication style: %s", style_id)
    return communication_style


@router.delete(
    "/communication-styles/{style_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir estilo",
    description="Exclui um estilo de comunicação se não estiver em uso por nenhuma campanha.",
)
@router.delete(
    "/personas/{style_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    include_in_schema=False
)
async def delete_communication_style(
    style_id: str,
    service: CommunicationStyleService = Depends(get_communication_style_service),
) -> None:
    """
    DELETE /api/communication-styles/{id} or /api/personas/{id}
    """
    service.delete_communication_style(style_id)
    logger.info("Deleted communication style: %s", style_id)
