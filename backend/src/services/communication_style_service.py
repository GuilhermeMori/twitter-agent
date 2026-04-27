"""
Communication Style Service — orchestrates communication style creation, retrieval, and management.
"""

import json
import math
from typing import List, Optional

import redis
from fastapi import HTTPException, status

from src.models.communication_style import (
    CommunicationStyle,
    CommunicationStyleSummary,
    CommunicationStyleCreateDTO,
    CommunicationStyleUpdateDTO,
)
from src.models.campaign import PaginatedResponse
from src.repositories.communication_style_repository import CommunicationStyleRepository
from src.core.logging_config import get_logger
from src.core.config import settings

logger = get_logger("services.communication_style_service")

COMMUNICATION_STYLE_CACHE_TTL = 3600
DEFAULT_COMMUNICATION_STYLE_CACHE_TTL = 300


class CommunicationStyleService:
    """Business logic for communication style management with Redis caching."""

    def __init__(self, repo: CommunicationStyleRepository, redis_client: Optional[redis.Redis] = None) -> None:
        self._repo = repo
        self._redis = redis_client or self._create_redis_client()

    def _create_redis_client(self) -> Optional[redis.Redis]:
        try:
            client = redis.from_url(settings.redis_url, decode_responses=True)
            client.ping()
            return client
        except Exception:
            return None

    def _cache_key(self, key_type: str, identifier: str = "") -> str:
        return f"communication_style:{key_type}:{identifier}" if identifier else f"communication_style:{key_type}"

    def _cache_get(self, key: str) -> Optional[dict]:
        if not self._redis:
            return None
        try:
            data = self._redis.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None

    def _cache_set(self, key: str, value: dict, ttl: int = COMMUNICATION_STYLE_CACHE_TTL) -> None:
        if not self._redis:
            return
        try:
            self._redis.setex(key, ttl, json.dumps(value))
        except Exception:
            pass

    def _cache_invalidate(self, style_id: Optional[str] = None) -> None:
        if not self._redis:
            return
        try:
            if style_id:
                self._redis.delete(self._cache_key("detail", style_id))
            for key in self._redis.scan_iter(match="communication_style:list:*"):
                self._redis.delete(key)
            self._redis.delete(self._cache_key("default"))
        except Exception:
            pass

    def create_communication_style(self, data: CommunicationStyleCreateDTO) -> str:
        try:
            total_count = self._repo.count_all()
            if total_count >= 50:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Limite de 50 estilos atingido.")
            if total_count == 0:
                data.is_default = True
            style_data = {
                "name": data.name, "title": data.title, "description": data.description,
                "tone_of_voice": data.tone_of_voice, "principles": data.principles,
                "vocabulary_allowed": data.vocabulary_allowed, "vocabulary_prohibited": data.vocabulary_prohibited,
                "formatting_rules": data.formatting_rules, "language": data.language,
                "system_prompt": data.system_prompt, "is_default": data.is_default,
            }
            created = self._repo.create(style_data)
            self._cache_invalidate()
            return created["id"]
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to create communication style: %s", str(e))
            raise HTTPException(status_code=500, detail="Failed to create communication style")

    def get_communication_style(self, style_id: str) -> CommunicationStyle:
        try:
            ck = self._cache_key("detail", style_id)
            cached = self._cache_get(ck)
            if cached:
                return CommunicationStyle(**cached)
            record = self._repo.get_by_id(style_id)
            if not record:
                raise HTTPException(status_code=404, detail=f"Communication style {style_id} not found")
            self._cache_set(ck, record)
            return CommunicationStyle(**record)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get communication style %s: %s", style_id, str(e))
            raise HTTPException(status_code=500, detail="Failed to retrieve communication style")

    def list_communication_styles(self, page: int = 1, limit: int = 20) -> PaginatedResponse[CommunicationStyle]:
        try:
            ck = self._cache_key("list", f"p{page}_l{limit}")
            cached = self._cache_get(ck)
            if cached:
                return PaginatedResponse(items=[CommunicationStyle(**r) for r in cached["items"]],
                                         total=cached["total"], page=cached["page"],
                                         limit=cached["limit"], total_pages=cached["total_pages"])
            offset = (page - 1) * limit
            items_raw = self._repo.list_all(limit=limit, offset=offset)
            total = self._repo.count_all()
            total_pages = math.ceil(total / limit) if total else 1
            self._cache_set(ck, {"items": items_raw, "total": total, "page": page, "limit": limit, "total_pages": total_pages})
            return PaginatedResponse(items=[CommunicationStyle(**r) for r in items_raw],
                                     total=total, page=page, limit=limit, total_pages=total_pages)
        except Exception as e:
            logger.error("Failed to list communication styles: %s", str(e))
            raise HTTPException(status_code=500, detail="Failed to list communication styles")

    def list_communication_style_summaries(self, page: int = 1, limit: int = 50) -> PaginatedResponse[CommunicationStyleSummary]:
        try:
            offset = (page - 1) * limit
            items_raw = self._repo.list_summaries(limit=limit, offset=offset)
            total = self._repo.count_all()
            total_pages = math.ceil(total / limit) if total else 1
            return PaginatedResponse(items=[CommunicationStyleSummary(**r) for r in items_raw],
                                     total=total, page=page, limit=limit, total_pages=total_pages)
        except Exception as e:
            logger.error("Failed to list summaries: %s", str(e))
            raise HTTPException(status_code=500, detail="Failed to list communication style summaries")

    def get_default_communication_style(self) -> CommunicationStyle:
        try:
            ck = self._cache_key("default")
            cached = self._cache_get(ck)
            if cached:
                return CommunicationStyle(**cached)
            record = self._repo.get_default()
            if not record:
                return self._create_default_style()
            self._cache_set(ck, record, DEFAULT_COMMUNICATION_STYLE_CACHE_TTL)
            return CommunicationStyle(**record)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get default communication style: %s", str(e))
            raise HTTPException(status_code=500, detail="Failed to get default communication style")

    def update_communication_style(self, style_id: str, data: CommunicationStyleUpdateDTO) -> CommunicationStyle:
        try:
            self.get_communication_style(style_id)
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            if not update_data:
                raise HTTPException(status_code=400, detail="No fields to update")
            updated = self._repo.update(style_id, update_data)
            self._cache_invalidate(style_id)
            return CommunicationStyle(**updated)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to update communication style %s: %s", style_id, str(e))
            raise HTTPException(status_code=500, detail="Failed to update communication style")

    def delete_communication_style(self, style_id: str) -> None:
        try:
            style = self.get_communication_style(style_id)
            campaigns = self._repo.check_usage_in_campaigns(style_id)
            if campaigns:
                names = [c["name"] for c in campaigns[:3]]
                more = f" e mais {len(campaigns) - 3}" if len(campaigns) > 3 else ""
                raise HTTPException(status_code=400, detail=f"Estilo em uso por: {', '.join(names)}{more}")
            if self._repo.count_all() <= 1:
                raise HTTPException(status_code=400, detail="Não é possível excluir o último estilo.")
            if style.is_default:
                self._set_new_default(style_id)
            self._repo.delete(style_id)
            self._cache_invalidate(style_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to delete communication style %s: %s", style_id, str(e))
            raise HTTPException(status_code=500, detail="Failed to delete communication style")

    def _set_new_default(self, excluding_id: str) -> None:
        try:
            styles = self._repo.list_all(limit=50, offset=0)
            available = [s for s in styles if s["id"] != excluding_id]
            if available:
                self._repo.update(available[0]["id"], {"is_default": True})
        except Exception:
            pass

    def _create_default_style(self) -> CommunicationStyle:
        default_data = CommunicationStyleCreateDTO(
            name="Strategic Partner", title="Social Media Copywriter",
            description="Strategic copywriter for Growth Collective. Interacts with DTC brand decision-makers.",
            tone_of_voice="Agile, reliable, consultative. Zero emojis. All comments in ENGLISH.",
            principles=["Hook First", "Real Personalization", "Short and Direct",
                         "Organic Engagement", "Value without Promotion", "Agility is Everything"],
            vocabulary_allowed=["Growth Collective", "Unified Strategy", "Scaling", "Strategic Partner"],
            vocabulary_prohibited=["Exclusive", "Check it out", "Best solution"],
            formatting_rules=["No Emojis", "Max 280 chars", "Line breaks for mobile", "No links"],
            language="en",
            system_prompt="You are a strategic copywriter for Growth Collective. Generate comments for DTC brand tweets. No emojis. Max 280 chars. Start with @username. ENGLISH only.",
            is_default=True,
        )
        style_id = self.create_communication_style(default_data)
        return self.get_communication_style(style_id)