import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import api from '../services/api'
import type { Campaign, Tweet, DownloadResponse, TweetWithAnalysisAndComment, CampaignResultsResponse, Persona } from '../types'
import DocumentViewer from '../components/DocumentViewer'
import TweetCardWithComment from '../components/TweetCardWithComment'
import { PersonaService } from '../services/personaService'
import { useNotification } from '../contexts/NotificationContext'

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { showToast, showConfirm } = useNotification()

  // State
  const [campaign, setCampaign] = useState<Campaign | null>(null)
  const [results, setResults] = useState<Tweet[]>([])
  const [enrichedResults, setEnrichedResults] = useState<TweetWithAnalysisAndComment[]>([])
  const [top3Ids, setTop3Ids] = useState<string[]>([])
  const [hasAnalysis, setHasAnalysis] = useState(false)
  const [hasComments, setHasComments] = useState(false)
  const [persona, setPersona] = useState<Persona | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)
  const [isViewerOpen, setIsViewerOpen] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [verdictFilter, setVerdictFilter] = useState<'ALL' | 'APPROVED' | 'REJECTED'>('ALL')
  const [deleting, setDeleting] = useState(false)
  const [retrying, setRetrying] = useState(false)
  const tweetsPerPage = 10

  // Load campaign details on mount
  useEffect(() => {
    if (id) {
      loadCampaignDetails()
    }
  }, [id])

  const loadCampaignDetails = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch campaign details
      const campaignResponse = await api.get<Campaign>(`/api/campaigns/${id}`)
      const camp = campaignResponse.data
      setCampaign(camp)

      // Fetch persona if campaign has one
      if (camp.persona_id) {
        try {
          const p = await PersonaService.getPersona(camp.persona_id)
          setPersona(p)
        } catch {
          // Non-critical — persona may have been deleted
        }
      }

      // Fetch results if campaign is completed
      if (camp.status === 'completed') {
        try {
          // Try enriched results first (analysis + comments)
          const enrichedResponse = await api.get<CampaignResultsResponse>(
            `/api/campaigns/${id}/results`
          )
          const data = enrichedResponse.data

          if (data.has_analysis || data.has_comments) {
            setEnrichedResults(data.tweets)
            setTop3Ids(data.top_3_tweet_ids || [])
            setHasAnalysis(data.has_analysis)
            setHasComments(data.has_comments)
          } else {
            // Fallback: plain tweet list
            setResults(data.tweets as unknown as Tweet[])
          }
        } catch {
          // Fallback to legacy endpoint
          const resultsResponse = await api.get<Tweet[]>(`/api/campaigns/${id}/results`)
          setResults(resultsResponse.data)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar detalhes da campanha')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadDocument = async () => {
    if (!campaign?.document_url) return

    try {
      setDownloading(true)
      const response = await api.get<DownloadResponse>(`/api/campaigns/${id}/download`)
      
      // Open download URL in new tab
      window.open(response.data.download_url, '_blank')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao baixar documento', 'error')
    } finally {
      setDownloading(false)
    }
  }

  const handleViewDocument = () => {
    if (!campaign?.document_url) return
    // Open document viewer modal
    setIsViewerOpen(true)
  }

  const handleRetryCampaign = async () => {
    if (!campaign) return
    
    showConfirm({
      title: 'Tentar Novamente',
      message: `Deseja reiniciar a execução da campanha "${campaign.name}"? Isso apagará os resultados atuais e iniciará uma nova busca.`,
      onConfirm: async () => {
        try {
          setRetrying(true)
          await api.post(`/api/campaigns/${id}/retry`)
          showToast('Campanha reenfileirada com sucesso!', 'success')
          // Reload details after a short delay
          setTimeout(loadCampaignDetails, 1000)
        } catch (err) {
          showToast(err instanceof Error ? err.message : 'Erro ao reiniciar campanha', 'error')
        } finally {
          setRetrying(false)
        }
      }
    })
  }

  const handleDeleteCampaign = async () => {
    if (!campaign) return
    
    showConfirm({
      title: 'Excluir Campanha',
      message: `Tem certeza que deseja excluir a campanha "${campaign.name}"? Esta ação não pode ser desfeita.`,
      isDanger: true,
      onConfirm: async () => {
        try {
          setDeleting(true)
          await api.delete(`/api/campaigns/${id}`)
          showToast('Campanha excluída com sucesso!', 'success')
          navigate('/history')
        } catch (err) {
          showToast(err instanceof Error ? err.message : 'Erro ao excluir campanha', 'error')
        } finally {
          setDeleting(false)
        }
      }
    })
  }

  const getStatusBadge = (status: Campaign['status']) => {
    const statusConfig = {
      pending: {
        bg: 'bg-yellow-100',
        text: 'text-yellow-800',
        border: 'border-yellow-200',
        label: 'Aguardando',
        icon: (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
              clipRule="evenodd"
            />
          </svg>
        ),
      },
      running: {
        bg: 'bg-blue-100',
        text: 'text-blue-800',
        border: 'border-blue-200',
        label: 'Em Execução',
        icon: (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-800"></div>
        ),
      },
      completed: {
        bg: 'bg-green-100',
        text: 'text-green-800',
        border: 'border-green-200',
        label: 'Concluída',
        icon: (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        ),
      },
      failed: {
        bg: 'bg-red-100',
        text: 'text-red-800',
        border: 'border-red-200',
        label: 'Falhou',
        icon: (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        ),
      },
    }

    const config = statusConfig[status]
    return (
      <span
        className={`inline-flex items-center space-x-2 px-4 py-2 rounded-full text-sm font-medium border ${config.bg} ${config.text} ${config.border}`}
      >
        {config.icon}
        <span>{config.label}</span>
      </span>
    )
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
          <p className="mt-4 text-gray-600">Carregando detalhes da campanha...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error || !campaign) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-start">
              <svg
                className="w-6 h-6 text-red-600 mt-0.5 mr-3 flex-shrink-0"
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
                <h3 className="text-lg font-medium text-red-800">Erro ao carregar campanha</h3>
                <p className="mt-2 text-sm text-red-700">{error || 'Campanha não encontrada'}</p>
                <button
                  onClick={() => navigate('/campaigns')}
                  className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium"
                >
                  Voltar ao Histórico
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/campaigns')}
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Voltar ao Histórico
          </button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{campaign.name}</h1>
              <p className="mt-2 text-sm text-gray-600">
                Criada em {formatDate(campaign.created_at)}
              </p>
            </div>
            <div className="flex items-center space-x-3">
              {getStatusBadge(campaign.status)}
              
              {campaign.status === 'failed' && (
                <button
                  onClick={handleRetryCampaign}
                  disabled={retrying}
                  className="inline-flex items-center px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:bg-gray-400 text-white rounded-lg text-sm font-medium shadow-sm hover:shadow-md transition-all duration-200"
                  title="Tentar novamente"
                >
                  {retrying ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Reiniciando...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Tentar Novamente
                    </>
                  )}
                </button>
              )}

              <button
                onClick={handleDeleteCampaign}
                disabled={deleting}
                className="inline-flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-lg text-sm font-medium shadow-sm hover:shadow-md transition-all duration-200"
                title="Excluir campanha"
              >
                {deleting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Excluindo...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    Excluir
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Configuration Section */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Configuração Utilizada</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Tipo de Busca</h3>
              <p className="text-base text-gray-900">
                {campaign.search_type === 'profile' ? 'Busca por Perfis' : 'Busca por Keywords'}
              </p>
            </div>

            {campaign.config.profiles && campaign.config.profiles.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Perfis</h3>
                <div className="flex flex-wrap gap-2">
                  {campaign.config.profiles.map((profile, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800 border border-blue-200"
                    >
                      @{profile}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {campaign.config.keywords && campaign.config.keywords.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Keywords</h3>
                <div className="flex flex-wrap gap-2">
                  {campaign.config.keywords.map((keyword, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-purple-100 text-purple-800 border border-purple-200"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Idioma</h3>
              <p className="text-base text-gray-900">{campaign.config.language}</p>
            </div>

            {(campaign.config.min_likes > 0 ||
              campaign.config.min_retweets > 0 ||
              campaign.config.min_replies > 0) && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Filtros de Engajamento</h3>
                <div className="space-y-1 text-sm text-gray-900">
                  {campaign.config.min_likes > 0 && (
                    <p>• Mínimo de {campaign.config.min_likes} likes</p>
                  )}
                  {campaign.config.min_retweets > 0 && (
                    <p>• Mínimo de {campaign.config.min_retweets} retweets</p>
                  )}
                  {campaign.config.min_replies > 0 && (
                    <p>• Mínimo de {campaign.config.min_replies} replies</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Persona Info */}
        {persona && (
          <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-3">Persona Utilizada</h2>
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium text-gray-900">{persona.name}</p>
                <p className="text-sm text-gray-600 mt-0.5">{persona.title}</p>
                <p className="text-sm text-gray-500 mt-1 line-clamp-2">{persona.description}</p>
              </div>
              <Link
                to={`/personas/${persona.id}`}
                className="ml-4 text-sm text-brand-600 hover:text-brand-700 font-medium whitespace-nowrap"
              >
                Ver persona ↗
              </Link>
            </div>
          </div>
        )}

        {/* Error Message (if failed) */}
        {campaign.status === 'failed' && campaign.error_message && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
            <div className="flex items-start">
              <svg
                className="w-6 h-6 text-red-600 mt-0.5 mr-3 flex-shrink-0"
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
                <h3 className="text-lg font-medium text-red-800">Erro na Execução</h3>
                <p className="mt-2 text-sm text-red-700">{campaign.error_message}</p>
                <button
                  onClick={handleRetryCampaign}
                  disabled={retrying}
                  className="mt-4 inline-flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium"
                >
                  {retrying ? 'Reiniciando...' : 'Tentar Novamente'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Document Actions (if document exists) */}
        {campaign.document_url && (
          <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Documento</h2>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleDownloadDocument}
                disabled={downloading}
                className="inline-flex items-center px-6 py-3 bg-brand-600 hover:bg-brand-700 disabled:bg-gray-400 text-white rounded-lg font-medium shadow-sm hover:shadow-md transition-all duration-200"
              >
                {downloading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Baixando...
                  </>
                ) : (
                  <>
                    <svg
                      className="w-5 h-5 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    Baixar Documento
                  </>
                )}
              </button>

              <button
                onClick={handleViewDocument}
                className="inline-flex items-center px-6 py-3 bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 rounded-lg font-medium shadow-sm hover:shadow-md transition-all duration-200"
              >
                <svg
                  className="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
                Visualizar Documento
              </button>
            </div>
          </div>
        )}

        {/* Results Section (if completed) */}
        {campaign.status === 'completed' && (
          <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Resultados</h2>
              <div className="flex items-center space-x-3">
                {hasAnalysis && (
                  <span className="text-xs bg-green-100 text-green-800 border border-green-200 rounded-full px-2.5 py-0.5 font-medium">
                    ✓ Com análise
                  </span>
                )}
                {hasComments && (
                  <span className="text-xs bg-blue-100 text-blue-800 border border-blue-200 rounded-full px-2.5 py-0.5 font-medium">
                    ✓ Com comentários
                  </span>
                )}
                <span className="text-sm text-gray-600">
                  {enrichedResults.length}{' '}
                  {enrichedResults.length === 1 ? 'tweet' : 'tweets'} coletados
                </span>
              </div>
              
              {/* Filter Buttons */}
              {(hasAnalysis) && (
                <div className="flex items-center space-x-2 mb-6">
                  <span className="text-sm font-medium text-gray-700 mr-2">Filtrar por:</span>
                  <button
                    onClick={() => { setVerdictFilter('ALL'); setCurrentPage(1); }}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                      verdictFilter === 'ALL' 
                        ? 'bg-brand-600 text-white shadow-sm' 
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    Todos
                  </button>
                  <button
                    onClick={() => { setVerdictFilter('APPROVED'); setCurrentPage(1); }}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                      verdictFilter === 'APPROVED' 
                        ? 'bg-green-600 text-white shadow-sm' 
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    ✓ Aprovados
                  </button>
                  <button
                    onClick={() => { setVerdictFilter('REJECTED'); setCurrentPage(1); }}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                      verdictFilter === 'REJECTED' 
                        ? 'bg-red-600 text-white shadow-sm' 
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    ✗ Rejeitados
                  </button>
                </div>
              )}
            </div>

            {/* Enriched results (with analysis + comments) */}
            {(hasAnalysis || hasComments) && enrichedResults.length > 0 ? (
              <>
                {(() => {
                  const filtered = enrichedResults.filter(item => {
                    if (verdictFilter === 'ALL') return true;
                    return item.analysis?.verdict === verdictFilter;
                  });
                  
                  const totalPages = Math.ceil(filtered.length / tweetsPerPage);
                  const currentTweets = filtered.slice((currentPage - 1) * tweetsPerPage, currentPage * tweetsPerPage);

                  if (filtered.length === 0) {
                    return (
                      <div className="text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                        <p className="text-gray-500">Nenhum tweet encontrado com este filtro.</p>
                      </div>
                    );
                  }

                  return (
                    <>
                      {filtered.length > tweetsPerPage && (
                        <div className="mb-4 flex items-center justify-between text-sm text-gray-600 bg-gray-50 px-4 py-2 rounded-lg">
                          <span>
                            Mostrando {(currentPage - 1) * tweetsPerPage + 1} até{' '}
                            {Math.min(currentPage * tweetsPerPage, filtered.length)} de{' '}
                            {filtered.length} tweets
                          </span>
                          <span>
                            Página {currentPage} de {totalPages}
                          </span>
                        </div>
                      )}

                      <div className="space-y-4">
                        {currentTweets.map(item => (
                          <TweetCardWithComment
                            key={item.id}
                            tweet={item}
                            analysis={item.analysis}
                            comment={item.comment}
                            isTop3={top3Ids.includes(item.id)}
                          />
                        ))}
                      </div>

                      {filtered.length > tweetsPerPage && (
                        <div className="mt-6 flex items-center justify-center space-x-4">
                          <button
                            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                            disabled={currentPage === 1}
                            className={`inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium ${
                              currentPage === 1
                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                : 'bg-white text-gray-700 hover:bg-gray-50'
                            }`}
                          >
                            ← Anterior
                          </button>
                          <span className="text-sm text-gray-600">
                            Página {currentPage} de {totalPages}
                          </span>
                          <button
                            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                            disabled={currentPage === totalPages}
                            className={`inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium ${
                              currentPage === totalPages
                                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                : 'bg-white text-gray-700 hover:bg-gray-50'
                            }`}
                          >
                            Próxima →
                          </button>
                        </div>
                      )}
                    </>
                  );
                })()}
              </>
            ) : results.length === 0 ? (
              <div className="text-center py-12">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                  />
                </svg>
                <p className="mt-4 text-gray-600">Nenhum tweet encontrado</p>
              </div>
            ) : (
              <>
                {/* Legacy plain tweet list */}
                {results.length > tweetsPerPage && (
                  <div className="mb-4 flex items-center justify-between text-sm text-gray-600 bg-gray-50 px-4 py-2 rounded-lg">
                    <span>
                      Mostrando {(currentPage - 1) * tweetsPerPage + 1} até{' '}
                      {Math.min(currentPage * tweetsPerPage, results.length)} de {results.length} tweets
                    </span>
                    <span>
                      Página {currentPage} de {Math.ceil(results.length / tweetsPerPage)}
                    </span>
                  </div>
                )}

                <div className="space-y-4">
                  {results
                    .slice((currentPage - 1) * tweetsPerPage, currentPage * tweetsPerPage)
                    .map((tweet) => (
                      <div
                        key={tweet.id}
                        className="border border-gray-200 rounded-lg p-5 hover:border-gray-300 hover:shadow-sm transition-all"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold text-gray-900">@{tweet.author}</span>
                            <span className="text-gray-400">•</span>
                            <span className="text-sm text-gray-500">
                              {new Intl.DateTimeFormat('pt-BR', {
                                day: '2-digit', month: '2-digit', year: 'numeric',
                                hour: '2-digit', minute: '2-digit', second: '2-digit',
                              }).format(new Date(tweet.timestamp))}
                            </span>
                          </div>
                          <a
                            href={tweet.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-sm text-brand-600 hover:text-brand-700 font-medium"
                          >
                            Ver no Twitter
                            <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                        </div>
                        <p className="text-gray-900 mb-4 whitespace-pre-wrap">{tweet.text}</p>
                        <div className="flex items-center space-x-6 text-sm text-gray-600">
                          <span>❤️ {new Intl.NumberFormat('pt-BR').format(tweet.likes)}</span>
                          <span>🔁 {new Intl.NumberFormat('pt-BR').format(tweet.reposts)}</span>
                          <span>💬 {new Intl.NumberFormat('pt-BR').format(tweet.replies)}</span>
                        </div>
                      </div>
                    ))}
                </div>

                {results.length > tweetsPerPage && (
                  <div className="mt-6 flex items-center justify-center space-x-4">
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className={`inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium ${
                        currentPage === 1 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      ← Anterior
                    </button>
                    <span className="text-sm text-gray-600">
                      Página {currentPage} de {Math.ceil(results.length / tweetsPerPage)}
                    </span>
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(Math.ceil(results.length / tweetsPerPage), prev + 1))}
                      disabled={currentPage === Math.ceil(results.length / tweetsPerPage)}
                      className={`inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium ${
                        currentPage === Math.ceil(results.length / tweetsPerPage) ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      Próxima →
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Pending/Running State */}
        {(campaign.status === 'pending' || campaign.status === 'running') && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-start">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3 mt-0.5"></div>
              <div>
                <h3 className="text-lg font-medium text-blue-800">
                  {campaign.status === 'pending'
                    ? 'Campanha Aguardando Execução'
                    : 'Campanha em Execução'}
                </h3>
                <p className="mt-2 text-sm text-blue-700">
                  {campaign.status === 'pending'
                    ? 'Sua campanha está na fila e será processada em breve.'
                    : 'Sua campanha está sendo processada. Os resultados aparecerão aqui quando concluída.'}
                </p>
                <button
                  onClick={loadCampaignDetails}
                  className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium"
                >
                  Atualizar Status
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Document Viewer Modal */}
        {campaign?.document_url && (
          <DocumentViewer
            documentUrl={campaign.document_url}
            isOpen={isViewerOpen}
            onClose={() => setIsViewerOpen(false)}
          />
        )}
      </div>
    </div>
  )
}
