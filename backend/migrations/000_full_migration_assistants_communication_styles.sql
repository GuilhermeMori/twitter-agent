-- ============================================================================
-- MIGRAÇÃO COMPLETA: Assistants + Communication Styles
-- ============================================================================
-- Execute este script no Supabase Dashboard > SQL Editor
-- Ele faz tudo de uma vez: cria assistants, renomeia personas, atualiza campaigns
-- ============================================================================

BEGIN;

-- ============================================================================
-- PASSO 1: Criar tabela de assistentes
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_assistants_role ON assistants(role);
CREATE INDEX IF NOT EXISTS idx_assistants_name ON assistants(name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_assistants_unique_role ON assistants(role);

-- Inserir os 3 assistentes fixos
INSERT INTO assistants (name, title, role, description, instructions, principles, quality_criteria, skills, is_editable)
VALUES (
    'Beto Busca',
    'Especialista em Pesquisa no Twitter',
    'search',
    'Especialista em pesquisa e monitoramento estratégico no Twitter/X para Growth Collective.',
    'Você é um analista de mercado com olhar aguçado para oportunidades de crescimento. Você não procura apenas por "posts de marketing"; você procura sinais de marcas que estão prontas para escalar mas estão "travadas". Foco em DTC/E-commerce, identificação de pain points, qualidade sobre quantidade.',
    '["Foco em DTC/E-commerce", "Identificação de Pain Points", "Qualidade sobre Quantidade", "Respeitar Limites", "Contexto Regional", "Sinais de Escala"]'::jsonb,
    '["Posts atendem likes/reposts mínimos", "Conteúdo relacionado aos critérios", "Lead time respeitado", "Dados completos e corretos"]'::jsonb,
    '["apify"]'::jsonb,
    TRUE
) ON CONFLICT DO NOTHING;

INSERT INTO assistants (name, title, role, description, instructions, principles, quality_criteria, skills, is_editable)
VALUES (
    'Cadu Comentário',
    'Copywriter de Mídias Sociais',
    'comment',
    'Copywriter estratégico para Growth Collective. Interage com posts de tomadores de decisão de marcas DTC.',
    'Você é um estrategista de marketing que fala a língua dos fundadores. Seja ágil, confiável e consultivo. Use quebras de linha para legibilidade mobile e foque em gerar valor antes de qualquer pitch.',
    '["Escolha o Gancho Primeiro", "Personalização Real", "Curto e Direto", "Engajamento Orgânico", "Valor sem Promoção", "Agilidade é Tudo"]'::jsonb,
    '["Gancho forte na primeira frase", "Avaliações com justificativa", "Check de Autenticidade", "Check de Segurança da Marca", "Limite de 280 caracteres", "Sem links", "Quebras de linha estratégicas"]'::jsonb,
    '[]'::jsonb,
    TRUE
) ON CONFLICT DO NOTHING;

INSERT INTO assistants (name, title, role, description, instructions, principles, quality_criteria, skills, is_editable)
VALUES (
    'Rita Revisão',
    'Guardiã de Qualidade e Segurança da Marca',
    'review',
    'Guardiã de qualidade e segurança da marca para Growth Collective. Analisa posts e comentários.',
    'Você é uma revisora com olho em ROAS e Brand Equity. Garante que nenhum comentário soe "vendedor" ou "desesperado". Use tabelas de pontuação e critérios claros para justificar vereditos (APPROVED ou REJECTED).',
    '["Veredito Baseado em Evidências", "Segurança Primeiro", "Foco em Relevância", "Alinhamento com Marca", "Critério de Gancho", "HITL (Human in the Loop)"]'::jsonb,
    '["Veredito final claro (APPROVED/REJECTED)", "Avaliações com justificativa", "Mudanças listadas se rejeitado", "Email com link e texto sugerido"]'::jsonb,
    '["blotato"]'::jsonb,
    TRUE
) ON CONFLICT DO NOTHING;

-- ============================================================================
-- PASSO 2: Renomear tabela personas para communication_styles
-- ============================================================================

ALTER TABLE IF EXISTS personas RENAME TO communication_styles;

-- Renomear índices (ignorar erros se não existirem)
DO $$
BEGIN
    EXECUTE 'ALTER INDEX IF EXISTS idx_personas_is_default RENAME TO idx_communication_styles_is_default';
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$
BEGIN
    EXECUTE 'ALTER INDEX IF EXISTS idx_personas_language RENAME TO idx_communication_styles_language';
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$
BEGIN
    EXECUTE 'ALTER INDEX IF EXISTS idx_personas_created_at RENAME TO idx_communication_styles_created_at';
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$
BEGIN
    EXECUTE 'ALTER INDEX IF EXISTS idx_personas_name RENAME TO idx_communication_styles_name';
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$
BEGIN
    EXECUTE 'ALTER INDEX IF EXISTS idx_personas_unique_default RENAME TO idx_communication_styles_unique_default';
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

COMMENT ON TABLE communication_styles IS 'Communication styles for generating tweet comments with specific tone and voice';

-- ============================================================================
-- PASSO 3: Atualizar referências em campaigns
-- ============================================================================

-- Renomear coluna persona_id para communication_style_id
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'campaigns' AND column_name = 'persona_id'
    ) THEN
        ALTER TABLE campaigns RENAME COLUMN persona_id TO communication_style_id;
    END IF;
END $$;

-- Atualizar foreign key
ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_persona_id_fkey;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'campaigns_communication_style_id_fkey'
    ) THEN
        ALTER TABLE campaigns ADD CONSTRAINT campaigns_communication_style_id_fkey 
            FOREIGN KEY (communication_style_id) REFERENCES communication_styles(id) ON DELETE RESTRICT;
    END IF;
END $$;

-- Renomear índice
DO $$
BEGIN
    EXECUTE 'ALTER INDEX IF EXISTS idx_campaigns_persona_id RENAME TO idx_campaigns_communication_style_id';
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

-- ============================================================================
-- VERIFICAÇÃO
-- ============================================================================

-- Verificar que tudo foi criado corretamente
DO $$
DECLARE
    assistant_count INTEGER;
    style_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO assistant_count FROM assistants;
    SELECT COUNT(*) INTO style_count FROM communication_styles;
    
    RAISE NOTICE '✅ Migração concluída!';
    RAISE NOTICE '   Assistentes: % registros', assistant_count;
    RAISE NOTICE '   Estilos de Comunicação: % registros', style_count;
    
    IF assistant_count < 3 THEN
        RAISE WARNING '⚠️ Menos de 3 assistentes encontrados!';
    END IF;
END $$;

COMMIT;