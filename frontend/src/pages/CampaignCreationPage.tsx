import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'
import { PersonaService } from '../services/personaService'
import { AssistantService } from '../services/assistantService'
import type { CampaignCreateDTO, SearchType, PersonaSummary, Assistant } from '../types'
import { useNotification } from '../contexts/NotificationContext'

export default function CampaignCreationPage() {
  const navigate = useNavigate()
  const { showToast } = useNotification()

  // Form state
  const [formData, setFormData] = useState<CampaignCreateDTO>({
    name: '',
    social_network: 'twitter',
    search_type: 'keywords',
    profiles: '',
    keywords: '',
    language: 'en',
    min_likes: 0,
    min_retweets: 0,
    min_replies: 0,
    days_back: 1,
    max_tweets: undefined,
    persona_id: undefined,
    communication_style_id: undefined,
  })

  // UI state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  // Persona / Communication Style state
  const [personas, setPersonas] = useState<PersonaSummary[]>([])
  const [personasLoading, setPersonasLoading] = useState(true)
  const [selectedPersona, setSelectedPersona] = useState<PersonaSummary | null>(null)

  // Assistants state
  const [assistants, setAssistants] = useState<Assistant[]>([])
  const [assistantsLoading, setAssistantsLoading] = useState(true)

  // Load personas and assistants
  useEffect(() => {
    const loadPersonas = async () => {
      try {
        setPersonasLoading(true)
        const response = await PersonaService.listPersonaSummaries(1, 50)
        setPersonas(response.items || [])

        // Pre-select default persona
        const defaultPersona = (response.items || []).find(p => p.is_default)
        if (defaultPersona) {
          setSelectedPersona(defaultPersona)
          setFormData(prev => ({ 
            ...prev, 
            persona_id: defaultPersona.id,
            communication_style_id: defaultPersona.id 
          }))
        }
      } catch {
        // Personas are optional — silently fail
      } finally {
        setPersonasLoading(false)
      }
    }

    const loadAssistants = async () => {
      try {
        setAssistantsLoading(true)
        const data = await AssistantService.listAssistants()
        setAssistants(data || [])
      } catch {
        // Assistants are optional — silently fail
      } finally {
        setAssistantsLoading(false)
      }
    }

    loadPersonas()
    loadAssistants()
  }, [])

  const handlePersonaChange = (personaId: string) => {
    if (personaId === '') {
      setSelectedPersona(null)
      setFormData(prev => ({ 
        ...prev, 
        persona_id: undefined,
        communication_style_id: undefined 
      }))
    } else {
      const persona = (personas || []).find(p => p.id === personaId) || null
      setSelectedPersona(persona)
      setFormData(prev => ({ 
        ...prev, 
        persona_id: personaId,
        communication_style_id: personaId 
      }))
    }
  }

  const handleInputChange = (field: keyof CampaignCreateDTO, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    // Clear validation error for this field when user starts typing
    if (validationErrors[field]) {
      setValidationErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
    // Clear error message when user modifies form
    if (error) {
      setError(null)
    }
  }

  const handleSearchTypeChange = (searchType: SearchType) => {
    setFormData((prev) => ({
      ...prev,
      search_type: searchType,
      // Clear the opposite field when switching
      profiles: searchType === 'keywords' ? '' : prev.profiles,
      keywords: searchType === 'profile' ? '' : prev.keywords,
    }))
    // Clear validation errors for both fields
    setValidationErrors((prev) => {
      const newErrors = { ...prev }
      delete newErrors.profiles
      delete newErrors.keywords
      return newErrors
    })
  }

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}

    // Campaign name validation
    if (!formData.name.trim()) {
      errors.name = 'Nome da campanha é obrigatório'
    }

    // Search type specific validation
    if (formData.search_type === 'profile') {
      if (!formData.profiles?.trim()) {
        errors.profiles = 'Pelo menos um perfil é obrigatório para busca por perfil'
      }
    } else if (formData.search_type === 'keywords') {
      if (!formData.keywords?.trim()) {
        errors.keywords = 'Pelo menos uma palavra-chave é obrigatória para busca por keywords'
      }
    }

    // Engagement filters validation (must be non-negative)
    if (formData.min_likes !== undefined && formData.min_likes < 0) {
      errors.min_likes = 'Valor não pode ser negativo'
    }
    if (formData.min_retweets !== undefined && formData.min_retweets < 0) {
      errors.min_retweets = 'Valor não pode ser negativo'
    }
    if (formData.min_replies !== undefined && formData.min_replies < 0) {
      errors.min_replies = 'Valor não pode ser negativo'
    }

    // Days back validation (1-365)
    if (formData.days_back !== undefined && (formData.days_back < 1 || formData.days_back > 365)) {
      errors.days_back = 'Deve estar entre 1 e 365 dias'
    }

    // Max tweets validation (1-200)
    if (formData.max_tweets !== undefined && formData.max_tweets !== null && (formData.max_tweets < 1 || formData.max_tweets > 200)) {
      errors.max_tweets = 'Deve estar entre 1 e 200 tweets'
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Clear previous error
    setError(null)

    // Validate form
    if (!validateForm()) {
      return
    }

    try {
      setLoading(true)
      await api.post<{ campaign_id: string; status: string }>(
        '/api/campaigns',
        formData
      )

      // Show success message
      const successMessage = `Campanha "${formData.name}" criada com sucesso! Redirecionando...`
      showToast(successMessage, 'success')

      // Redirect to history after 3 seconds
      setTimeout(() => {
        navigate('/history')
      }, 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar campanha')
      setLoading(false)
    }
  }

  const handleCancel = () => {
    // Reset form
    setFormData({
      name: '',
      social_network: 'twitter',
      search_type: 'keywords',
      profiles: '',
      keywords: '',
      language: 'en',
      min_likes: 0,
      min_retweets: 0,
      min_replies: 0,
      days_back: 1,
      max_tweets: undefined,
      persona_id: undefined,
    })
    setValidationErrors({})
    setError(null)
    setSelectedPersona(null)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Nova Campanha</h1>
          <p className="mt-2 text-gray-600">
            Configure e execute uma nova campanha de scraping do Twitter.
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
            <svg
              className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <h3 className="text-sm font-medium text-red-800">Erro ao criar campanha</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Campaign Form */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200">
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Campaign Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Nome da Campanha *
              </label>
              <input
                id="name"
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors ${
                  validationErrors.name ? 'border-red-300 bg-red-50' : 'border-gray-300 bg-white'
                }`}
                placeholder="Ex: Monitoramento de IA - Janeiro 2024"
                disabled={loading}
              />
              {validationErrors.name && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.name}</p>
              )}
            </div>

            {/* Search Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Tipo de Busca *
              </label>
              <div className="flex space-x-4">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    name="search_type"
                    value="profile"
                    checked={formData.search_type === 'profile'}
                    onChange={() => handleSearchTypeChange('profile')}
                    className="w-4 h-4 text-brand-600 focus:ring-brand-500 border-gray-300"
                    disabled={loading}
                  />
                  <span className="ml-2 text-sm text-gray-700">Busca por Perfis</span>
                </label>
                <label className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    name="search_type"
                    value="keywords"
                    checked={formData.search_type === 'keywords'}
                    onChange={() => handleSearchTypeChange('keywords')}
                    className="w-4 h-4 text-brand-600 focus:ring-brand-500 border-gray-300"
                    disabled={loading}
                  />
                  <span className="ml-2 text-sm text-gray-700">Busca por Palavras-chave</span>
                </label>
              </div>
            </div>

            {/* Conditional: Profiles Field */}
            {formData.search_type === 'profile' && (
              <div>
                <label htmlFor="profiles" className="block text-sm font-medium text-gray-700 mb-2">
                  Perfis do Twitter *
                </label>
                <textarea
                  id="profiles"
                  value={formData.profiles}
                  onChange={(e) => handleInputChange('profiles', e.target.value)}
                  rows={4}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors ${
                    validationErrors.profiles
                      ? 'border-red-300 bg-red-50'
                      : 'border-gray-300 bg-white'
                  }`}
                  placeholder="@elonmusk, @naval, @sama&#10;ou um perfil por linha"
                  disabled={loading}
                />
                {validationErrors.profiles && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.profiles}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Insira perfis separados por vírgula ou quebra de linha. O símbolo @ é opcional.
                </p>
              </div>
            )}

            {/* Conditional: Keywords Field */}
            {formData.search_type === 'keywords' && (
              <div>
                <label htmlFor="keywords" className="block text-sm font-medium text-gray-700 mb-2">
                  Palavras-chave *
                </label>
                <textarea
                  id="keywords"
                  value={formData.keywords}
                  onChange={(e) => handleInputChange('keywords', e.target.value)}
                  rows={4}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors ${
                    validationErrors.keywords
                      ? 'border-red-300 bg-red-50'
                      : 'border-gray-300 bg-white'
                  }`}
                  placeholder="artificial intelligence, machine learning, AI&#10;ou uma palavra-chave por linha"
                  disabled={loading}
                />
                {validationErrors.keywords && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.keywords}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Insira palavras-chave separadas por vírgula ou quebra de linha.
                </p>
              </div>
            )}

            {/* ─── Pipeline de Assistentes ─────────────────────────────────── */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3">Pipeline de Assistentes</h3>
              <p className="text-xs text-gray-500 mb-4">
                Cada campanha usa 3 assistentes de IA, um para cada etapa do pipeline. No futuro você poderá escolher entre diferentes assistentes para cada função.
              </p>

              {assistantsLoading ? (
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
                  <span>Carregando assistentes...</span>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {['search', 'comment', 'review'].map((role) => {
                    const assistant = (assistants || []).find(a => a.role === role)
                    if (!assistant) return null
                    const icon = AssistantService.getRoleIcon(role)
                    const roleLabel = AssistantService.getRoleDisplay(role)
                    const color = AssistantService.getRoleColor(role)

                    return (
                      <div key={role} className={`${color.bg} border ${color.border} rounded-lg p-3`}>
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-lg">{icon}</span>
                          <span className={`text-xs font-semibold uppercase tracking-wide ${color.text}`}>{roleLabel}</span>
                        </div>
                        <p className="text-sm font-medium text-gray-900">{assistant.name}</p>
                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{assistant.title}</p>
                        <Link
                          to={`/assistants/${assistant.id}/edit`}
                          className={`inline-block mt-2 text-xs font-medium ${color.text} hover:underline`}
                        >
                          Editar →
                        </Link>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* ─── Estilo de Comunicação ──────────────────────────────────── */}
            <div>
              <label htmlFor="persona_id" className="block text-sm font-medium text-gray-700 mb-2">
                Estilo de Comunicação
              </label>
              <p className="text-xs text-gray-500 mb-3">
                Define o tom de voz e as regras que o assistente de comentários (Cadu) usa para gerar respostas.
              </p>
              {personasLoading ? (
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
                  <span>Carregando estilos...</span>
                </div>
              ) : (personas?.length ?? 0) === 0 ? (
                <div className="flex items-center space-x-2 text-sm text-gray-500 bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
                  <span>Nenhum estilo disponível.</span>
                  <Link to="/personas/create" className="text-brand-600 hover:text-brand-700 font-medium">
                    Criar um estilo
                  </Link>
                </div>
              ) : (
                <>
                  <select
                    id="persona_id"
                    value={formData.persona_id || ''}
                    onChange={(e) => handlePersonaChange(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors bg-white"
                    disabled={loading}
                  >
                    <option value="">Sem estilo (sem geração de comentários)</option>
                    {(personas || []).map(persona => (
                      <option key={persona.id} value={persona.id}>
                        {persona.name} — {persona.title}
                        {persona.is_default ? ' (padrão)' : ''}
                      </option>
                    ))}
                  </select>

                  {selectedPersona && (
                    <div className="mt-3 bg-green-50 border border-green-200 rounded-lg px-4 py-3 flex items-start justify-between">
                      <div>
                        <p className="text-sm font-medium text-green-900">{selectedPersona.name}</p>
                        <p className="text-xs text-green-700 mt-0.5">{selectedPersona.title}</p>
                        {selectedPersona.is_default && (
                          <span className="inline-block mt-1 text-xs bg-yellow-100 text-yellow-800 border border-yellow-200 rounded-full px-2 py-0.5">
                            Estilo padrão
                          </span>
                        )}
                      </div>
                      <Link
                        to={`/personas/${selectedPersona.id}`}
                        className="text-xs text-green-600 hover:text-green-800 font-medium ml-4 whitespace-nowrap"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Ver detalhes ↗
                      </Link>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Language */}
            <div>
              <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-2">
                Idioma
              </label>
              <select
                id="language"
                value={formData.language}
                onChange={(e) => handleInputChange('language', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors bg-white"
                disabled={loading}
              >
                <option value="en">Inglês</option>
                <option value="pt">Português</option>
                <option value="es">Espanhol</option>
                <option value="fr">Francês</option>
                <option value="de">Alemão</option>
                <option value="it">Italiano</option>
                <option value="ja">Japonês</option>
                <option value="ko">Coreano</option>
                <option value="zh">Chinês</option>
              </select>
            </div>

            {/* Days Back */}
            <div>
              <label htmlFor="days_back" className="block text-sm font-medium text-gray-700 mb-2">
                Período de Busca (dias) *
              </label>
              <input
                id="days_back"
                type="number"
                min="1"
                max="365"
                value={formData.days_back}
                onChange={(e) => handleInputChange('days_back', parseInt(e.target.value) || 1)}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors ${
                  validationErrors.days_back
                    ? 'border-red-300 bg-red-50'
                    : 'border-gray-300 bg-white'
                }`}
                placeholder="1"
                disabled={loading}
              />
              {validationErrors.days_back && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.days_back}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Buscar tweets dos últimos X dias (1 = ontem, 7 = última semana, 30 = último mês). Máximo: 365 dias.
              </p>
            </div>

            {/* Max Tweets */}
            <div>
              <label htmlFor="max_tweets" className="block text-sm font-medium text-gray-700 mb-2">
                Máximo de Tweets para Analisar (opcional)
              </label>
              <input
                id="max_tweets"
                type="number"
                min="1"
                max="200"
                value={formData.max_tweets || ''}
                onChange={(e) => {
                  const value = e.target.value ? parseInt(e.target.value) || 0 : 0
                  setFormData(prev => ({ ...prev, max_tweets: value > 0 ? value : undefined }))
                  if (validationErrors.max_tweets) {
                    setValidationErrors(prev => {
                      const newErrors = { ...prev }
                      delete newErrors.max_tweets
                      return newErrors
                    })
                  }
                }}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors ${
                  validationErrors.max_tweets
                    ? 'border-red-300 bg-red-50'
                    : 'border-gray-300 bg-white'
                }`}
                placeholder="Sem limite (analisar todos)"
                disabled={loading}
              />
              {validationErrors.max_tweets && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.max_tweets}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Limita a análise aos X tweets com maior engajamento (likes + retweets + replies). Deixe vazio para analisar todos os tweets encontrados. Máximo: 200.
              </p>
            </div>

            {/* Engagement Filters */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Filtros de Engajamento (opcional)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Min Likes */}
                <div>
                  <label
                    htmlFor="min_likes"
                    className="block text-sm font-medium text-gray-600 mb-2"
                  >
                    Mínimo de Likes
                  </label>
                  <input
                    id="min_likes"
                    type="number"
                    min="0"
                    value={formData.min_likes}
                    onChange={(e) => handleInputChange('min_likes', parseInt(e.target.value) || 0)}
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors ${
                      validationErrors.min_likes
                        ? 'border-red-300 bg-red-50'
                        : 'border-gray-300 bg-white'
                    }`}
                    placeholder="0"
                    disabled={loading}
                  />
                  {validationErrors.min_likes && (
                    <p className="mt-1 text-sm text-red-600">{validationErrors.min_likes}</p>
                  )}
                </div>

                {/* Min Retweets */}
                <div>
                  <label
                    htmlFor="min_retweets"
                    className="block text-sm font-medium text-gray-600 mb-2"
                  >
                    Mínimo de Retweets
                  </label>
                  <input
                    id="min_retweets"
                    type="number"
                    min="0"
                    value={formData.min_retweets}
                    onChange={(e) =>
                      handleInputChange('min_retweets', parseInt(e.target.value) || 0)
                    }
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors ${
                      validationErrors.min_retweets
                        ? 'border-red-300 bg-red-50'
                        : 'border-gray-300 bg-white'
                    }`}
                    placeholder="0"
                    disabled={loading}
                  />
                  {validationErrors.min_retweets && (
                    <p className="mt-1 text-sm text-red-600">{validationErrors.min_retweets}</p>
                  )}
                </div>

                {/* Min Replies */}
                <div>
                  <label
                    htmlFor="min_replies"
                    className="block text-sm font-medium text-gray-600 mb-2"
                  >
                    Mínimo de Respostas
                  </label>
                  <input
                    id="min_replies"
                    type="number"
                    min="0"
                    value={formData.min_replies}
                    onChange={(e) =>
                      handleInputChange('min_replies', parseInt(e.target.value) || 0)
                    }
                    className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors ${
                      validationErrors.min_replies
                        ? 'border-red-300 bg-red-50'
                        : 'border-gray-300 bg-white'
                    }`}
                    placeholder="0"
                    disabled={loading}
                  />
                  {validationErrors.min_replies && (
                    <p className="mt-1 text-sm text-red-600">{validationErrors.min_replies}</p>
                  )}
                </div>
              </div>
              <p className="mt-2 text-xs text-gray-500">
                Apenas tweets que atendam a todos os filtros especificados serão coletados. Deixe
                em 0 para não aplicar filtro.
              </p>
            </div>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start">
              <svg
                className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
              <div>
                <h3 className="text-sm font-medium text-blue-800">Execução Automática</h3>
                <p className="mt-1 text-sm text-blue-700">
                  Após criar a campanha, ela será executada automaticamente. Você receberá um email
                  quando os resultados estiverem prontos.
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end space-x-4 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={handleCancel}
                disabled={loading}
                className="px-6 py-2.5 rounded-lg font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={loading}
                className={`px-6 py-2.5 rounded-lg font-medium text-white transition-all duration-200 flex items-center space-x-2 ${
                  loading
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-brand-600 hover:bg-brand-700 shadow-sm hover:shadow-md'
                }`}
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Criando Campanha...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 4v16m8-8H4"
                      />
                    </svg>
                    <span>Criar Campanha</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Help Section */}
        <div className="mt-8 bg-white shadow-sm rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Dicas</h2>
          <div className="space-y-3 text-sm text-gray-600">
            <div className="flex items-start">
              <svg
                className="w-5 h-5 text-brand-600 mt-0.5 mr-2 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <p>
                <strong>Busca por Perfis:</strong> Ideal para monitorar tweets de usuários
                específicos. Use @ antes do nome ou apenas o nome de usuário.
              </p>
            </div>
            <div className="flex items-start">
              <svg
                className="w-5 h-5 text-brand-600 mt-0.5 mr-2 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <p>
                <strong>Busca por Palavras-chave:</strong> Ideal para descobrir conversas sobre
                tópicos específicos. Use termos relevantes ao seu interesse.
              </p>
            </div>
            <div className="flex items-start">
              <svg
                className="w-5 h-5 text-brand-600 mt-0.5 mr-2 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <p>
                <strong>Filtros de Engajamento:</strong> Use para focar em tweets com maior
                relevância. Valores mais altos resultam em menos tweets, mas mais engajados.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
