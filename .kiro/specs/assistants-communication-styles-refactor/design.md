# Design Document

## Introduction

Este documento especifica o design técnico para refatorar o sistema de "Personas" em dois conceitos distintos:

1. **Assistentes (Assistants)**: Agentes especializados que executam tarefas específicas no pipeline
2. **Estilos de Comunicação (Communication Styles)**: Configurações de tom de voz e estilo para geração de comentários

Esta refatoração visa separar claramente as responsabilidades e permitir que usuários leigos possam editar assistentes e criar estilos de comunicação de forma intuitiva através do frontend.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │   Assistants     │  │    Communication Styles              │ │
│  │   Management     │  │    Management                        │ │
│  │   - List (3)     │  │    - List (CRUD)                     │ │
│  │   - Edit         │  │    - Create/Edit/Delete              │ │
│  └──────────────────┘  └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │  Assistants API  │  │  Communication Styles API            │ │
│  │  /api/assistants │  │  /api/communication-styles           │ │
│  └──────────────────┘  └──────────────────────────────────────┘ │
│                              │                                   │
│  ┌──────────────────────────┴────────────────────────────────┐ │
│  │              Services Layer                                │ │
│  │  - AssistantService                                        │ │
│  │  - CommunicationStyleService                               │ │
│  │  - CommentGenerationService (updated)                      │ │
│  │  - CommentReviewService (updated)                          │ │
│  │  - SearchService (updated)                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌──────────────────────────┴────────────────────────────────┐ │
│  │              Repository Layer                              │ │
│  │  - AssistantRepository                                     │ │
│  │  - CommunicationStyleRepository                            │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Database (PostgreSQL/Supabase)                │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │   assistants     │  │   communication_styles               │ │
│  │   (3 records)    │  │   (renamed from personas)            │ │
│  └──────────────────┘  └──────────────────────────────────────┘ │
│                              │                                   │
│  ┌──────────────────────────┴────────────────────────────────┐ │
│  │              campaigns                                     │ │
│  │              - communication_style_id (FK)                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

#### Comment Generation Flow
```
1. User creates Campaign → selects Communication Style
2. Campaign Executor starts
3. SearchService uses Assistant Beto → finds posts
4. For each post:
   a. CommentGenerationService:
      - Fetches Assistant Cadu (role='comment')
      - Fetches Communication Style from campaign
      - Combines: Cadu.instructions + Style.system_prompt
      - Generates comment via OpenAI
   b. CommentReviewService:
      - Fetches Assistant Rita (role='review')
      - Reviews comment using Rita.quality_criteria
      - Returns APPROVED/REJECTED
5. Approved comments sent to user
```

## Data Models

### Database Schema

#### Table: assistants (NEW)

```sql
CREATE TABLE assistants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('search', 'comment', 'review')),
    description TEXT NOT NULL,
    instructions TEXT NOT NULL,
    principles JSONB NOT NULL DEFAULT '[]'::jsonb,
    quality_criteria JSONB NOT NULL DEFAULT '[]'::jsonb,
    skills JSONB DEFAULT '[]'::jsonb,
    is_editable BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_assistants_role ON assistants(role);
CREATE INDEX idx_assistants_name ON assistants(name);

-- Unique constraint on role (only one assistant per role)
CREATE UNIQUE INDEX idx_assistants_unique_role ON assistants(role);

-- Comments
COMMENT ON TABLE assistants IS 'AI assistants that execute specific tasks in the pipeline';
COMMENT ON COLUMN assistants.role IS 'Assistant role: search, comment, or review';
COMMENT ON COLUMN assistants.instructions IS 'Detailed instructions for the assistant';
COMMENT ON COLUMN assistants.principles IS 'JSON array of principles the assistant follows';
COMMENT ON COLUMN assistants.quality_criteria IS 'JSON array of quality criteria for evaluation';
COMMENT ON COLUMN assistants.skills IS 'JSON array of skills/tools the assistant can use (e.g., ["apify", "blotato"])';
```

#### Table: communication_styles (RENAMED from personas)

```sql
-- Rename table
ALTER TABLE personas RENAME TO communication_styles;

-- Update indexes
ALTER INDEX idx_personas_is_default RENAME TO idx_communication_styles_is_default;
ALTER INDEX idx_personas_language RENAME TO idx_communication_styles_language;
ALTER INDEX idx_personas_created_at RENAME TO idx_communication_styles_created_at;
ALTER INDEX idx_personas_name RENAME TO idx_communication_styles_name;
ALTER INDEX idx_personas_unique_default RENAME TO idx_communication_styles_unique_default;

-- Update comments
COMMENT ON TABLE communication_styles IS 'Communication styles for generating tweet comments with specific tone and voice';
```

#### Table: campaigns (UPDATED)

```sql
-- Rename column
ALTER TABLE campaigns RENAME COLUMN persona_id TO communication_style_id;

-- Update foreign key constraint
ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_persona_id_fkey;
ALTER TABLE campaigns ADD CONSTRAINT campaigns_communication_style_id_fkey 
    FOREIGN KEY (communication_style_id) REFERENCES communication_styles(id);

-- Update index
ALTER INDEX idx_campaigns_persona_id RENAME TO idx_campaigns_communication_style_id;
```

### Initial Data - Assistants

#### 1. Beto Busca (Search Assistant)

```json
{
  "name": "Beto Busca",
  "title": "Especialista em Pesquisa no Twitter",
  "role": "search",
  "description": "Especialista em pesquisa e monitoramento estratégico no Twitter/X para Growth Collective. Sua função principal é varrer a rede em busca de Founders, CEOs e CMOs de marcas DTC e e-commerce faturando entre $3-5M que estão travados e procurando insights de marketing de performance e parcerias estratégicas.",
  "instructions": "Você é um analista de mercado com olhar aguçado para oportunidades de crescimento. Você não procura apenas por 'posts de marketing'; você procura sinais de marcas que estão prontas para escalar mas estão 'travadas'. Você entende a dor de fundadores que se sentem queimados por agências e busca conversas onde a Growth Collective pode se posicionar como o parceiro estratégico definitivo.\n\nFoco em DTC/E-commerce, identificação de pain points, qualidade sobre quantidade. Priorize conversas sobre ROAS, Meta Ads, Google Ads, email marketing e retenção para marcas de 7 e 8 dígitos.",
  "principles": [
    "Foco em DTC/E-commerce — Priorize marcas e fundadores no espaço direct-to-consumer",
    "Identificação de Pain Points — Procure posts onde fundadores expressam frustração com crescimento ou gestão de mídia",
    "Qualidade sobre Quantidade — É melhor entregar 10 posts de tomadores de decisão reais do que 20 de 'gurus' de marketing",
    "Respeitar Limites — Use Apify de forma eficiente para evitar desperdício de tokens e tempo",
    "Contexto Regional — Foque principalmente nos mercados dos EUA e Canadá",
    "Sinais de Escala — Valide se a marca mencionada ou o perfil do autor se encaixa no perfil de receita $3-5M"
  ],
  "quality_criteria": [
    "Posts encontrados atendem aos likes e reposts mínimos configurados",
    "Conteúdo do post está diretamente relacionado aos critérios da Growth Collective",
    "O intervalo de tempo (lead time) respeita o limite definido (ex: 1 hora)",
    "Dados do post (link, autor, texto, métricas) estão completos e corretos"
  ],
  "skills": ["apify"]
}
```


#### 2. Cadu Comentário (Comment Assistant)

```json
{
  "name": "Cadu Comentário",
  "title": "Copywriter de Mídias Sociais",
  "role": "comment",
  "description": "Copywriter estratégico para Growth Collective. Sua missão é interagir com posts de tomadores de decisão de marcas DTC, propondo insights que posicionam a Growth Collective como o parceiro 'all-in-one' (Meta, Google, Creative, Email e Estratégia) que desbloqueará o crescimento da marca.",
  "instructions": "Você é um estrategista de marketing que fala a língua dos fundadores. Você não é apenas um 'gerente de mídias sociais'; você é um parceiro estratégico. Você entende CPA, LTV e escalonamento vertical/horizontal. Sua voz é de alguém que viu marcas 'queimadas' por agências e sabe que a solução real requer uma visão holística, não apenas compra de mídia.\n\nSeja ágil, confiável e consultivo. Use quebras de linha para legibilidade mobile e foque em gerar valor antes de qualquer pitch. Soe como um par para os fundadores, não um bot de vendas.",
  "principles": [
    "Escolha o Gancho Primeiro — A primeira frase deve parar o scroll e fazer o autor (e seus seguidores) lerem o resto",
    "Personalização Real — Cada resposta deve mostrar que o post original foi realmente lido e compreendido",
    "Curto e Direto — Respeite os limites do Twitter e a atenção limitada dos usuários",
    "Engajamento Orgânico — Termine de forma que a conversa continue naturalmente, seja através de uma opinião forte, concordância ou uma pergunta real",
    "Valor sem Promoção — Entregue insights genuínos ou reações antes de qualquer menção à Growth Collective",
    "Agilidade é Tudo — Proponha textos que soem atuais e conectados ao momento do post"
  ],
  "quality_criteria": [
    "A primeira frase é um gancho forte (para o scroll)",
    "Qualquer avaliação (1 a 10) tem justificativa",
    "Se rejeitado, as mudanças necessárias estão listadas",
    "Check de Autenticidade: O comentário soa humano ou está preso no padrão de pergunta final?",
    "Check de Segurança da Marca: O comentário está 100% livre de emojis?",
    "O texto sugerido respeita o limite de 280 caracteres",
    "Não há links no corpo do comentário",
    "Uso estratégico de quebras de linha para legibilidade mobile"
  ],
  "skills": []
}
```

#### 3. Rita Revisão (Review Assistant)

```json
{
  "name": "Rita Revisão",
  "title": "Guardiã de Qualidade e Segurança da Marca",
  "role": "review",
  "description": "Guardiã de qualidade e segurança da marca para Growth Collective. Seu papel é analisar cada post monitorado e cada comentário sugerido para garantir que a interação seja valiosa, segura e alinhada com os critérios de excelência de uma consultoria estratégica de elite.",
  "instructions": "Você é uma revisora com olho em ROAS e Brand Equity. Você entende que a Growth Collective não é apenas uma agência de execução, mas um parceiro estratégico. Você garante que nenhum comentário soe 'vendedor' ou 'desesperado', mas sim uma contribuição intelectual de alto nível para a discussão de crescimento.\n\nSeja direta, imparcial e extremamente estruturada. Use tabelas de pontuação e critérios claros para justificar seus vereditos (APPROVED ou REJECTED). Foque em garantir que o tom de voz 'Strategic Partner' seja mantido em todas as interações.",
  "principles": [
    "Veredito Baseado em Evidências — Cada pontuação deve ser acompanhada de justificativa baseada em critérios de qualidade",
    "Segurança Primeiro — Qualquer sinal de conteúdo ofensivo, sensacionalista ou controverso no post original deve causar rejeição imediata da interação",
    "Foco em Relevância — O comentário realmente adiciona valor à conversa ou é apenas ruído?",
    "Alinhamento com Marca — O tom de voz reflete a identidade da Growth Collective?",
    "Critério de Gancho — O primeiro parágrafo é forte o suficiente para parar o scroll?",
    "HITL (Human in the Loop) — Garanta que o usuário receba as informações corretas no email para tomar a decisão final de aprovação"
  ],
  "quality_criteria": [
    "O veredito final é claro (APPROVED ou REJECTED)",
    "Todas as avaliações (1 a 10) têm justificativa",
    "Em caso de rejeição, as mudanças necessárias estão listadas",
    "O email de notificação (via Blotato) contém o link para o post e o texto sugerido"
  ],
  "skills": ["blotato"]
}
```

## API Design

### Assistants API

#### Endpoints

**Base Path:** `/api/assistants`

##### 1. List Assistants
```http
GET /api/assistants
```

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Beto Busca",
      "title": "Especialista em Pesquisa no Twitter",
      "role": "search",
      "description": "...",
      "instructions": "...",
      "principles": ["..."],
      "quality_criteria": ["..."],
      "skills": ["apify"],
      "is_editable": true,
      "created_at": "2026-04-25T10:00:00Z",
      "updated_at": "2026-04-25T10:00:00Z"
    }
  ],
  "total": 3,
  "page": 1,
  "limit": 20,
  "total_pages": 1
}
```

##### 2. Get Assistant by ID
```http
GET /api/assistants/{id}
```

**Response 200:**
```json
{
  "id": "uuid",
  "name": "Cadu Comentário",
  "title": "Copywriter de Mídias Sociais",
  "role": "comment",
  "description": "...",
  "instructions": "...",
  "principles": ["..."],
  "quality_criteria": ["..."],
  "skills": [],
  "is_editable": true,
  "created_at": "2026-04-25T10:00:00Z",
  "updated_at": "2026-04-25T10:00:00Z"
}
```

**Response 404:**
```json
{
  "detail": "Assistant {id} not found"
}
```

##### 3. Update Assistant
```http
PUT /api/assistants/{id}
```

**Request Body:**
```json
{
  "name": "Beto Busca Atualizado",
  "description": "Nova descrição...",
  "instructions": "Novas instruções...",
  "principles": ["Princípio 1", "Princípio 2"],
  "quality_criteria": ["Critério 1", "Critério 2"],
  "skills": ["apify"]
}
```

**Response 200:**
```json
{
  "id": "uuid",
  "name": "Beto Busca Atualizado",
  ...
}
```

**Response 400:**
```json
{
  "detail": "No fields to update"
}
```

**Response 404:**
```json
{
  "detail": "Assistant {id} not found"
}
```

##### 4. Create Assistant (BLOCKED)
```http
POST /api/assistants
```

**Response 405:**
```json
{
  "detail": "Creating assistants is not allowed. The system has exactly 3 fixed assistants."
}
```

##### 5. Delete Assistant (BLOCKED)
```http
DELETE /api/assistants/{id}
```

**Response 405:**
```json
{
  "detail": "Deleting assistants is not allowed. The system requires exactly 3 fixed assistants."
}
```

### Communication Styles API

#### Endpoints

**Base Path:** `/api/communication-styles`

##### 1. List Communication Styles
```http
GET /api/communication-styles?page=1&limit=20
```

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Cadu Copy",
      "title": "Copywriter Estratégico",
      "description": "...",
      "tone_of_voice": "...",
      "principles": ["..."],
      "vocabulary_allowed": ["..."],
      "vocabulary_prohibited": ["..."],
      "formatting_rules": ["..."],
      "language": "pt",
      "system_prompt": "...",
      "is_default": true,
      "created_at": "2026-04-25T10:00:00Z",
      "updated_at": "2026-04-25T10:00:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "limit": 20,
  "total_pages": 1
}
```

##### 2. Get Communication Style by ID
```http
GET /api/communication-styles/{id}
```

**Response 200:**
```json
{
  "id": "uuid",
  "name": "Cadu Copy",
  ...
}
```

##### 3. Create Communication Style
```http
POST /api/communication-styles
```

**Request Body:**
```json
{
  "name": "Novo Estilo",
  "title": "Título do Estilo",
  "description": "Descrição...",
  "tone_of_voice": "Tom de voz...",
  "principles": ["Princípio 1"],
  "vocabulary_allowed": ["palavra1"],
  "vocabulary_prohibited": ["palavra2"],
  "formatting_rules": ["regra1"],
  "language": "pt",
  "system_prompt": "Prompt completo...",
  "is_default": false
}
```

**Response 201:**
```json
{
  "communication_style_id": "uuid",
  "message": "Communication style created successfully"
}
```

##### 4. Update Communication Style
```http
PUT /api/communication-styles/{id}
```

**Request Body:** (same as create, all fields optional)

**Response 200:**
```json
{
  "id": "uuid",
  "name": "Estilo Atualizado",
  ...
}
```

##### 5. Delete Communication Style
```http
DELETE /api/communication-styles/{id}
```

**Response 204:** (No content)

**Response 400:**
```json
{
  "detail": "Cannot delete communication style. It is used by campaigns: Campaign 1, Campaign 2"
}
```

## Backend Implementation

### Pydantic Models

#### Assistant Models

```python
from pydantic import BaseModel, field_validator
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID

class Assistant(BaseModel):
    """Full assistant record."""
    id: UUID
    name: str
    title: str
    role: Literal['search', 'comment', 'review']
    description: str
    instructions: str
    principles: List[str]
    quality_criteria: List[str]
    skills: List[str]
    is_editable: bool
    created_at: datetime
    updated_at: datetime

class AssistantSummary(BaseModel):
    """Simplified assistant for lists."""
    id: UUID
    name: str
    title: str
    role: Literal['search', 'comment', 'review']
    is_editable: bool

class AssistantUpdateDTO(BaseModel):
    """Assistant update data transfer object."""
    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    principles: Optional[List[str]] = None
    quality_criteria: Optional[List[str]] = None
    skills: Optional[List[str]] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Assistant name cannot be empty")
        return v.strip() if v else v

    @field_validator("principles")
    @classmethod
    def principles_valid(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            if len(v) == 0:
                raise ValueError("At least one principle is required")
            cleaned = [p.strip() for p in v if p and p.strip()]
            if not cleaned:
                raise ValueError("At least one non-empty principle is required")
            return cleaned
        return v
```


#### Communication Style Models (Renamed from Persona)

```python
# Rename all Persona* models to CommunicationStyle*

class CommunicationStyle(BaseModel):
    """Full communication style record (renamed from Persona)."""
    id: UUID
    name: str
    title: str
    description: str
    tone_of_voice: str
    principles: List[str]
    vocabulary_allowed: Optional[List[str]] = None
    vocabulary_prohibited: Optional[List[str]] = None
    formatting_rules: Optional[List[str]] = None
    language: str
    system_prompt: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

class CommunicationStyleSummary(BaseModel):
    """Simplified communication style for lists and dropdowns."""
    id: UUID
    name: str
    title: str
    language: str
    is_default: bool
    created_at: datetime

class CommunicationStyleCreateDTO(BaseModel):
    """Communication style creation DTO (renamed from PersonaCreateDTO)."""
    name: str
    title: str
    description: str
    tone_of_voice: str
    principles: List[str]
    vocabulary_allowed: Optional[List[str]] = None
    vocabulary_prohibited: Optional[List[str]] = None
    formatting_rules: Optional[List[str]] = None
    language: str = "pt"
    system_prompt: str
    is_default: bool = False
    
    # Same validators as PersonaCreateDTO

class CommunicationStyleUpdateDTO(BaseModel):
    """Communication style update DTO (renamed from PersonaUpdateDTO)."""
    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tone_of_voice: Optional[str] = None
    principles: Optional[List[str]] = None
    vocabulary_allowed: Optional[List[str]] = None
    vocabulary_prohibited: Optional[List[str]] = None
    formatting_rules: Optional[List[str]] = None
    language: Optional[str] = None
    system_prompt: Optional[str] = None
    is_default: Optional[bool] = None
    
    # Same validators as PersonaUpdateDTO
```

### Services

#### AssistantService

```python
from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from src.repositories.assistant_repository import AssistantRepository
from src.models.assistant import Assistant, AssistantUpdateDTO

class AssistantService:
    """Business logic for assistant management."""

    def __init__(self, repo: AssistantRepository) -> None:
        self._repo = repo

    def list_assistants(self) -> List[Assistant]:
        """
        List all 3 assistants.
        
        Returns:
            List of all assistants
        """
        try:
            records = self._repo.list_all()
            return [Assistant(**r) for r in records]
        except Exception as e:
            logger.error("Failed to list assistants: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list assistants",
            )

    def get_assistant(self, assistant_id: str) -> Assistant:
        """
        Get assistant by ID.
        
        Args:
            assistant_id: UUID string
            
        Returns:
            Assistant object
            
        Raises:
            HTTPException: If not found
        """
        try:
            record = self._repo.get_by_id(assistant_id)
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assistant {assistant_id} not found",
                )
            return Assistant(**record)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get assistant %s: %s", assistant_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve assistant",
            )

    def get_assistant_by_role(self, role: str) -> Assistant:
        """
        Get assistant by role (search, comment, review).
        
        Args:
            role: Assistant role
            
        Returns:
            Assistant object
            
        Raises:
            HTTPException: If not found
        """
        try:
            record = self._repo.get_by_role(role)
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assistant with role '{role}' not found",
                )
            return Assistant(**record)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get assistant by role %s: %s", role, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve assistant",
            )

    def update_assistant(self, assistant_id: str, data: AssistantUpdateDTO) -> Assistant:
        """
        Update an assistant.
        
        Args:
            assistant_id: UUID string
            data: Update data
            
        Returns:
            Updated assistant
            
        Raises:
            HTTPException: If not found or update fails
        """
        try:
            # Verify assistant exists
            self.get_assistant(assistant_id)

            # Convert DTO to dict, excluding None values
            update_data = {}
            for field, value in data.model_dump().items():
                if value is not None:
                    update_data[field] = value

            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update",
                )

            updated = self._repo.update(assistant_id, update_data)
            logger.info("Assistant %s updated", assistant_id)
            
            return Assistant(**updated)

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to update assistant %s: %s", assistant_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update assistant",
            )
```

#### CommunicationStyleService (Renamed from PersonaService)

```python
# Rename PersonaService to CommunicationStyleService
# Update all references from persona to communication_style
# Keep same logic and methods

class CommunicationStyleService:
    """Business logic for communication style management (renamed from PersonaService)."""

    def __init__(self, repo: CommunicationStyleRepository, redis_client: Optional[redis.Redis] = None) -> None:
        self._repo = repo
        self._redis = redis_client or self._create_redis_client()

    # All methods remain the same, just rename:
    # - create_persona → create_communication_style
    # - get_persona → get_communication_style
    # - list_personas → list_communication_styles
    # - update_persona → update_communication_style
    # - delete_persona → delete_communication_style
    # - get_default_persona → get_default_communication_style
    
    # Update cache keys from "persona:" to "communication_style:"
    # Update all internal references
```

#### Updated CommentGenerationService

```python
class CommentGenerationService:
    """Service for generating tweet comments using assistants and communication styles."""

    def __init__(
        self,
        openai_client,
        assistant_service: AssistantService,
        communication_style_service: CommunicationStyleService,
        comment_repo: TweetCommentRepository,
        validator: CommentValidator
    ):
        self._openai = openai_client
        self._assistant_service = assistant_service
        self._style_service = communication_style_service
        self._comment_repo = comment_repo
        self._validator = validator

    async def generate_comment(
        self,
        tweet: Tweet,
        campaign_id: str,
        communication_style_id: str
    ) -> TweetComment:
        """
        Generate a comment for a tweet using Assistant Cadu + Communication Style.
        
        Args:
            tweet: Tweet object
            campaign_id: Campaign ID
            communication_style_id: Communication style ID
            
        Returns:
            Generated comment
        """
        try:
            # 1. Get Assistant Cadu (role='comment')
            assistant = self._assistant_service.get_assistant_by_role('comment')
            
            # 2. Get Communication Style
            style = self._style_service.get_communication_style(communication_style_id)
            
            # 3. Combine instructions from assistant + system_prompt from style
            combined_prompt = f"""{assistant.instructions}

---

{style.system_prompt}

---

TWEET TO RESPOND TO:
Author: @{tweet.author_username}
Text: {tweet.text}

Generate a comment following all the principles and rules above."""

            # 4. Generate comment using OpenAI
            response = await self._openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": combined_prompt},
                    {"role": "user", "content": f"Generate a comment for this tweet: {tweet.text}"}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            comment_text = response.choices[0].message.content.strip()
            
            # 5. Validate comment
            validation_result = self._validator.validate_comment(
                comment=comment_text,
                communication_style=style,
                tweet_author=tweet.author_username
            )
            
            # 6. Save comment
            comment = self._comment_repo.create({
                "tweet_id": tweet.id,
                "campaign_id": campaign_id,
                "comment_text": comment_text,
                "is_valid": validation_result.is_valid,
                "validation_errors": validation_result.errors,
                "status": "pending_review"
            })
            
            return comment
            
        except Exception as e:
            logger.error("Failed to generate comment: %s", str(e))
            raise
```

### Repositories

#### AssistantRepository

```python
from typing import List, Optional, Dict, Any
from supabase import Client

class AssistantRepository:
    """Repository for assistant database operations."""

    def __init__(self, db: Client) -> None:
        self._db = db

    def list_all(self) -> List[Dict[str, Any]]:
        """
        List all assistants (always 3).
        
        Returns:
            List of assistant records
        """
        try:
            result = (
                self._db.table("assistants")
                .select("*")
                .order("role")  # search, comment, review
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error("Failed to list assistants: %s", str(e))
            raise

    def get_by_id(self, assistant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get assistant by ID.
        
        Args:
            assistant_id: UUID string
            
        Returns:
            Assistant record or None
        """
        try:
            result = (
                self._db.table("assistants")
                .select("*")
                .eq("id", assistant_id)
                .execute()
            )
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Failed to get assistant %s: %s", assistant_id, str(e))
            raise

    def get_by_role(self, role: str) -> Optional[Dict[str, Any]]:
        """
        Get assistant by role.
        
        Args:
            role: Assistant role (search, comment, review)
            
        Returns:
            Assistant record or None
        """
        try:
            result = (
                self._db.table("assistants")
                .select("*")
                .eq("role", role)
                .limit(1)
                .execute()
            )
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            logger.error("Failed to get assistant by role %s: %s", role, str(e))
            raise

    def update(self, assistant_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an assistant.
        
        Args:
            assistant_id: UUID string
            update_data: Fields to update
            
        Returns:
            Updated assistant record
        """
        try:
            update_data["updated_at"] = "now()"
            
            result = (
                self._db.table("assistants")
                .update(update_data)
                .eq("id", assistant_id)
                .execute()
            )
            
            if not result.data:
                raise Exception(f"Assistant {assistant_id} not found")
                
            return result.data[0]
        except Exception as e:
            logger.error("Failed to update assistant %s: %s", assistant_id, str(e))
            raise
```

#### CommunicationStyleRepository (Renamed from PersonaRepository)

```python
# Rename PersonaRepository to CommunicationStyleRepository
# Update all table references from "personas" to "communication_styles"
# Update all column references from "persona_id" to "communication_style_id"
# Keep same methods and logic

class CommunicationStyleRepository:
    """Repository for communication style database operations."""

    def __init__(self, db: Client) -> None:
        self._db = db

    # All methods remain the same, just update table name:
    # self._db.table("personas") → self._db.table("communication_styles")
    
    def check_usage_in_campaigns(self, style_id: str) -> List[Dict[str, Any]]:
        """Check if communication style is used in any campaigns."""
        try:
            result = (
                self._db.table("campaigns")
                .select("id, name, status, created_at")
                .eq("communication_style_id", style_id)  # Updated column name
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error("Failed to check style usage %s: %s", style_id, str(e))
            raise
```

## Frontend Implementation

### Pages

#### 1. AssistantListPage.tsx

```typescript
/**
 * Assistant List Page
 * 
 * Displays the 3 fixed assistants with edit functionality.
 * No create/delete options.
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { PencilIcon } from '@heroicons/react/24/outline'
import { AssistantService } from '../services/assistantService'
import type { Assistant } from '../types'

export default function AssistantListPage() {
  const navigate = useNavigate()
  const [assistants, setAssistants] = useState<Assistant[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAssistants()
  }, [])

  const loadAssistants = async () => {
    try {
      setLoading(true)
      const data = await AssistantService.listAssistants()
      setAssistants(data)
    } catch (error) {
      console.error('Failed to load assistants:', error)
    } finally {
      setLoading(false)
    }
  }

  const getIcon = (role: string) => {
    switch (role) {
      case 'search': return '🔍'
      case 'comment': return '✍️'
      case 'review': return '🛡️'
      default: return '🤖'
    }
  }

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'search': return 'Busca'
      case 'comment': return 'Comentário'
      case 'review': return 'Revisão'
      default: return role
    }
  }

  if (loading) {
    return <div className="flex justify-center p-8">Carregando...</div>
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Assistentes</h1>
        <p className="mt-2 text-gray-600">
          Gerencie os 3 assistentes que executam tarefas no sistema
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {assistants.map((assistant) => (
          <div
            key={assistant.id}
            className="bg-white shadow rounded-lg p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center">
                <span className="text-4xl mr-3">{getIcon(assistant.role)}</span>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {assistant.name}
                  </h3>
                  <p className="text-sm text-gray-600">{assistant.title}</p>
                  <span className="inline-block mt-1 px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                    {getRoleLabel(assistant.role)}
                  </span>
                </div>
              </div>
            </div>

            <p className="mt-4 text-sm text-gray-700 line-clamp-3">
              {assistant.description}
            </p>

            <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
              <span>{assistant.principles.length} princípios</span>
              <span>{assistant.quality_criteria.length} critérios</span>
            </div>

            <button
              onClick={() => navigate(`/assistants/${assistant.id}/edit`)}
              className="mt-4 w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <PencilIcon className="h-4 w-4 mr-2" />
              Editar Assistente
            </button>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-md p-4">
        <p className="text-sm text-blue-800">
          <strong>Nota:</strong> Os assistentes são fixos no sistema. Você pode editar suas instruções e princípios, mas não pode criar novos ou excluir os existentes.
        </p>
      </div>
    </div>
  )
}
```


#### 2. AssistantEditPage.tsx

```typescript
/**
 * Assistant Edit Page
 * 
 * Form for editing an assistant's configuration.
 * Simple interface for non-technical users.
 */

import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeftIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { AssistantService } from '../services/assistantService'
import type { Assistant, AssistantUpdateDTO } from '../types'

export default function AssistantEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  
  const [assistant, setAssistant] = useState<Assistant | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    title: '',
    description: '',
    instructions: '',
    principles: [] as string[],
    quality_criteria: [] as string[],
    skills: [] as string[]
  })
  
  const [newPrinciple, setNewPrinciple] = useState('')
  const [newCriterion, setNewCriterion] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (id) {
      loadAssistant(id)
    }
  }, [id])

  const loadAssistant = async (assistantId: string) => {
    try {
      setLoading(true)
      const data = await AssistantService.getAssistant(assistantId)
      setAssistant(data)
      setFormData({
        name: data.name,
        title: data.title,
        description: data.description,
        instructions: data.instructions,
        principles: data.principles,
        quality_criteria: data.quality_criteria,
        skills: data.skills
      })
    } catch (err) {
      setError('Falha ao carregar assistente')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!id) return

    try {
      setSaving(true)
      setError(null)
      
      const updateData: AssistantUpdateDTO = {
        name: formData.name,
        title: formData.title,
        description: formData.description,
        instructions: formData.instructions,
        principles: formData.principles.filter(p => p.trim()),
        quality_criteria: formData.quality_criteria.filter(c => c.trim()),
        skills: formData.skills
      }

      await AssistantService.updateAssistant(id, updateData)
      navigate('/assistants')
    } catch (err) {
      setError('Falha ao salvar assistente')
    } finally {
      setSaving(false)
    }
  }

  const addPrinciple = () => {
    if (newPrinciple.trim()) {
      setFormData(prev => ({
        ...prev,
        principles: [...prev.principles, newPrinciple.trim()]
      }))
      setNewPrinciple('')
    }
  }

  const removePrinciple = (index: number) => {
    setFormData(prev => ({
      ...prev,
      principles: prev.principles.filter((_, i) => i !== index)
    }))
  }

  const addCriterion = () => {
    if (newCriterion.trim()) {
      setFormData(prev => ({
        ...prev,
        quality_criteria: [...prev.quality_criteria, newCriterion.trim()]
      }))
      setNewCriterion('')
    }
  }

  const removeCriterion = (index: number) => {
    setFormData(prev => ({
      ...prev,
      quality_criteria: prev.quality_criteria.filter((_, i) => i !== index)
    }))
  }

  if (loading) {
    return <div className="flex justify-center p-8">Carregando...</div>
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <button
          onClick={() => navigate('/assistants')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeftIcon className="h-5 w-5 mr-2" />
          Voltar para Assistentes
        </button>
        <h1 className="text-3xl font-bold text-gray-900">
          Editar Assistente: {assistant?.name}
        </h1>
        <p className="mt-2 text-gray-600">
          Personalize as instruções e princípios do assistente
        </p>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Informações Básicas
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Nome
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Título
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Descrição
                <span className="text-gray-500 font-normal ml-2">
                  (Resumo do que o assistente faz)
                </span>
              </label>
              <textarea
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Instruções
                <span className="text-gray-500 font-normal ml-2">
                  (Instruções detalhadas para o assistente)
                </span>
              </label>
              <textarea
                rows={8}
                value={formData.instructions}
                onChange={(e) => setFormData(prev => ({ ...prev, instructions: e.target.value }))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 font-mono text-sm"
                required
              />
            </div>
          </div>
        </div>

        {/* Principles */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Princípios
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Princípios que guiam o comportamento do assistente
          </p>

          <div className="space-y-2 mb-4">
            {formData.principles.map((principle, index) => (
              <div key={index} className="flex items-start space-x-2">
                <span className="flex-1 text-sm text-gray-700 bg-gray-50 px-3 py-2 rounded">
                  {principle}
                </span>
                <button
                  type="button"
                  onClick={() => removePrinciple(index)}
                  className="text-red-600 hover:text-red-800 p-2"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>
            ))}
          </div>

          <div className="flex space-x-2">
            <input
              type="text"
              value={newPrinciple}
              onChange={(e) => setNewPrinciple(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addPrinciple())}
              className="flex-1 border border-gray-300 rounded-md shadow-sm py-2 px-3"
              placeholder="Adicione um princípio..."
            />
            <button
              type="button"
              onClick={addPrinciple}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <PlusIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Quality Criteria */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Critérios de Qualidade
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Critérios usados para avaliar a qualidade do trabalho do assistente
          </p>

          <div className="space-y-2 mb-4">
            {formData.quality_criteria.map((criterion, index) => (
              <div key={index} className="flex items-start space-x-2">
                <span className="flex-1 text-sm text-gray-700 bg-gray-50 px-3 py-2 rounded">
                  {criterion}
                </span>
                <button
                  type="button"
                  onClick={() => removeCriterion(index)}
                  className="text-red-600 hover:text-red-800 p-2"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>
            ))}
          </div>

          <div className="flex space-x-2">
            <input
              type="text"
              value={newCriterion}
              onChange={(e) => setNewCriterion(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCriterion())}
              className="flex-1 border border-gray-300 rounded-md shadow-sm py-2 px-3"
              placeholder="Adicione um critério..."
            />
            <button
              type="button"
              onClick={addCriterion}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <PlusIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/assistants')}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Salvando...' : 'Salvar Alterações'}
          </button>
        </div>
      </form>
    </div>
  )
}
```

### Services

#### AssistantService.ts

```typescript
/**
 * Assistant API Service
 */

import api from './api'
import type { Assistant, AssistantUpdateDTO } from '../types'

export class AssistantService {
  private static readonly BASE_PATH = '/assistants'

  /**
   * List all assistants (always 3)
   */
  static async listAssistants(): Promise<Assistant[]> {
    try {
      const response = await api.get<{ items: Assistant[] }>(this.BASE_PATH)
      return response.data.items
    } catch (error) {
      console.error('Failed to list assistants:', error)
      throw new Error('Falha ao carregar assistentes')
    }
  }

  /**
   * Get assistant by ID
   */
  static async getAssistant(assistantId: string): Promise<Assistant> {
    try {
      const response = await api.get<Assistant>(`${this.BASE_PATH}/${assistantId}`)
      return response.data
    } catch (error) {
      console.error(`Failed to get assistant ${assistantId}:`, error)
      throw new Error('Falha ao carregar assistente')
    }
  }

  /**
   * Update assistant
   */
  static async updateAssistant(
    assistantId: string,
    data: AssistantUpdateDTO
  ): Promise<Assistant> {
    try {
      const response = await api.put<Assistant>(`${this.BASE_PATH}/${assistantId}`, data)
      return response.data
    } catch (error) {
      console.error(`Failed to update assistant ${assistantId}:`, error)
      throw new Error('Falha ao atualizar assistente')
    }
  }
}
```

#### CommunicationStyleService.ts (Renamed from PersonaService)

```typescript
/**
 * Communication Style API Service (renamed from PersonaService)
 */

import api from './api'
import type {
  CommunicationStyle,
  CommunicationStyleCreateDTO,
  CommunicationStyleUpdateDTO,
  CommunicationStyleSummary,
  PaginatedResponse,
  CreateCommunicationStyleResponse
} from '../types'

export class CommunicationStyleService {
  private static readonly BASE_PATH = '/communication-styles'

  // All methods same as PersonaService, just:
  // - Update BASE_PATH
  // - Rename types from Persona* to CommunicationStyle*
  // - Update error messages

  static async createCommunicationStyle(data: CommunicationStyleCreateDTO): Promise<CreateCommunicationStyleResponse> {
    try {
      const response = await api.post<CreateCommunicationStyleResponse>(this.BASE_PATH, data)
      return response.data
    } catch (error) {
      console.error('Failed to create communication style:', error)
      throw new Error('Falha ao criar estilo de comunicação')
    }
  }

  static async listCommunicationStyles(
    page: number = 1,
    limit: number = 20
  ): Promise<PaginatedResponse<CommunicationStyle>> {
    try {
      const response = await api.get<PaginatedResponse<CommunicationStyle>>(this.BASE_PATH, {
        params: { page, limit }
      })
      return response.data
    } catch (error) {
      console.error('Failed to list communication styles:', error)
      throw new Error('Falha ao carregar estilos de comunicação')
    }
  }

  // ... other methods (same as PersonaService)
}
```

## Migration Scripts

### Migration 1: Create Assistants Table

```sql
-- Migration: Create assistants table and populate with 3 fixed assistants
-- Date: 2026-04-25

BEGIN;

-- Create assistants table
CREATE TABLE IF NOT EXISTS assistants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('search', 'comment', 'review')),
    description TEXT NOT NULL,
    instructions TEXT NOT NULL,
    principles JSONB NOT NULL DEFAULT '[]'::jsonb,
    quality_criteria JSONB NOT NULL DEFAULT '[]'::jsonb,
    skills JSONB DEFAULT '[]'::jsonb,
    is_editable BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_assistants_role ON assistants(role);
CREATE INDEX idx_assistants_name ON assistants(name);
CREATE UNIQUE INDEX idx_assistants_unique_role ON assistants(role);

-- Add comments
COMMENT ON TABLE assistants IS 'AI assistants that execute specific tasks in the pipeline';
COMMENT ON COLUMN assistants.role IS 'Assistant role: search, comment, or review';

-- Insert 3 fixed assistants
INSERT INTO assistants (name, title, role, description, instructions, principles, quality_criteria, skills)
VALUES
-- Beto Busca (Search)
(
    'Beto Busca',
    'Especialista em Pesquisa no Twitter',
    'search',
    'Especialista em pesquisa e monitoramento estratégico no Twitter/X para Growth Collective...',
    'Você é um analista de mercado com olhar aguçado para oportunidades de crescimento...',
    '["Foco em DTC/E-commerce", "Identificação de Pain Points", "Qualidade sobre Quantidade", "Respeitar Limites", "Contexto Regional", "Sinais de Escala"]'::jsonb,
    '["Posts encontrados atendem aos likes e reposts mínimos", "Conteúdo relacionado aos critérios", "Intervalo de tempo respeitado", "Dados completos e corretos"]'::jsonb,
    '["apify"]'::jsonb
),
-- Cadu Comentário (Comment)
(
    'Cadu Comentário',
    'Copywriter de Mídias Sociais',
    'comment',
    'Copywriter estratégico para Growth Collective...',
    'Você é um estrategista de marketing que fala a língua dos fundadores...',
    '["Escolha o Gancho Primeiro", "Personalização Real", "Curto e Direto", "Engajamento Orgânico", "Valor sem Promoção", "Agilidade é Tudo"]'::jsonb,
    '["Gancho forte", "Avaliações justificadas", "Mudanças listadas se rejeitado", "Check de Autenticidade", "Check de Segurança da Marca", "Limite de 280 caracteres", "Sem links", "Quebras de linha estratégicas"]'::jsonb,
    '[]'::jsonb
),
-- Rita Revisão (Review)
(
    'Rita Revisão',
    'Guardiã de Qualidade e Segurança da Marca',
    'review',
    'Guardiã de qualidade e segurança da marca para Growth Collective...',
    'Você é uma revisora com olho em ROAS e Brand Equity...',
    '["Veredito Baseado em Evidências", "Segurança Primeiro", "Foco em Relevância", "Alinhamento com Marca", "Critério de Gancho", "HITL (Human in the Loop)"]'::jsonb,
    '["Veredito claro", "Avaliações justificadas", "Mudanças listadas se rejeitado", "Email com link e texto"]'::jsonb,
    '["blotato"]'::jsonb
);

COMMIT;
```

### Migration 2: Rename Personas to Communication Styles

```sql
-- Migration: Rename personas table to communication_styles
-- Date: 2026-04-25

BEGIN;

-- Rename table
ALTER TABLE personas RENAME TO communication_styles;

-- Rename indexes
ALTER INDEX idx_personas_is_default RENAME TO idx_communication_styles_is_default;
ALTER INDEX idx_personas_language RENAME TO idx_communication_styles_language;
ALTER INDEX idx_personas_created_at RENAME TO idx_communication_styles_created_at;
ALTER INDEX idx_personas_name RENAME TO idx_communication_styles_name;
ALTER INDEX idx_personas_unique_default RENAME TO idx_communication_styles_unique_default;

-- Update table comment
COMMENT ON TABLE communication_styles IS 'Communication styles for generating tweet comments with specific tone and voice';

-- Rename column in campaigns table
ALTER TABLE campaigns RENAME COLUMN persona_id TO communication_style_id;

-- Drop old foreign key constraint
ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_persona_id_fkey;

-- Add new foreign key constraint
ALTER TABLE campaigns ADD CONSTRAINT campaigns_communication_style_id_fkey 
    FOREIGN KEY (communication_style_id) REFERENCES communication_styles(id);

-- Rename index
ALTER INDEX idx_campaigns_persona_id RENAME TO idx_campaigns_communication_style_id;

COMMIT;
```

### Rollback Script

```sql
-- Rollback: Revert refactoring changes
-- Date: 2026-04-25

BEGIN;

-- Revert campaigns table
ALTER TABLE campaigns RENAME COLUMN communication_style_id TO persona_id;
ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_communication_style_id_fkey;
ALTER TABLE campaigns ADD CONSTRAINT campaigns_persona_id_fkey 
    FOREIGN KEY (persona_id) REFERENCES communication_styles(id);
ALTER INDEX idx_campaigns_communication_style_id RENAME TO idx_campaigns_persona_id;

-- Revert communication_styles to personas
ALTER INDEX idx_communication_styles_is_default RENAME TO idx_personas_is_default;
ALTER INDEX idx_communication_styles_language RENAME TO idx_personas_language;
ALTER INDEX idx_communication_styles_created_at RENAME TO idx_personas_created_at;
ALTER INDEX idx_communication_styles_name RENAME TO idx_personas_name;
ALTER INDEX idx_communication_styles_unique_default RENAME TO idx_personas_unique_default;
ALTER TABLE communication_styles RENAME TO personas;
COMMENT ON TABLE personas IS 'AI personas for generating tweet comments';

-- Drop assistants table
DROP TABLE IF EXISTS assistants CASCADE;

COMMIT;
```

## Testing Strategy

### Unit Tests

1. **AssistantService Tests**
   - Test list_assistants returns 3 assistants
   - Test get_assistant_by_role for each role
   - Test update_assistant with valid data
   - Test update_assistant with invalid data

2. **CommunicationStyleService Tests**
   - Test CRUD operations
   - Test default style management
   - Test usage validation before delete

3. **CommentGenerationService Tests**
   - Test comment generation with assistant + style
   - Test prompt combination logic
   - Test validation integration

### Integration Tests

1. **API Tests**
   - Test all assistant endpoints
   - Test all communication style endpoints
   - Test error responses (405 for create/delete assistants)

2. **Database Tests**
   - Test migrations run successfully
   - Test rollback works correctly
   - Test foreign key constraints

### End-to-End Tests

1. **User Workflows**
   - Edit assistant and verify changes persist
   - Create communication style and use in campaign
   - Delete unused communication style
   - Attempt to delete style in use (should fail)

## Deployment Plan

### Phase 1: Database Migration
1. Backup current database
2. Run migration 1 (create assistants table)
3. Run migration 2 (rename personas)
4. Verify data integrity

### Phase 2: Backend Deployment
1. Deploy new models and services
2. Deploy new API endpoints
3. Run integration tests
4. Monitor for errors

### Phase 3: Frontend Deployment
1. Deploy new pages and components
2. Update navigation
3. Test user workflows
4. Monitor user feedback

### Phase 4: Cleanup
1. Remove old code references
2. Update documentation
3. Archive old migrations

## Monitoring and Rollback

### Monitoring
- Track API error rates
- Monitor database query performance
- Track user adoption of new features

### Rollback Triggers
- Critical bugs affecting campaigns
- Data integrity issues
- High error rates (>5%)

### Rollback Procedure
1. Stop new deployments
2. Run rollback migration script
3. Deploy previous backend version
4. Deploy previous frontend version
5. Verify system stability
