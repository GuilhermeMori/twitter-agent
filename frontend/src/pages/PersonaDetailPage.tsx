/**
 * Persona Detail Page (Estilo de Comunicação)
 * 
 * Exibe a visualização detalhada de um estilo de comunicação.
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { 
  PencilIcon, 
  TrashIcon, 
  ArrowLeftIcon,
  ExclamationTriangleIcon,
  StarIcon as StarIconSolid,
  StarIcon as StarIconOutline
} from '@heroicons/react/24/outline'
import { PersonaService } from '../services/personaService'
import type { Persona } from '../types'
import { useNotification } from '../contexts/NotificationContext'

export default function PersonaDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { showToast, showConfirm } = useNotification()
  
  const [persona, setPersona] = useState<Persona | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)

  const loadPersona = async () => {
    if (!id) { setError('ID inválido'); setLoading(false); return }
    try {
      setLoading(true); setError(null)
      setPersona(await PersonaService.getPersona(id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar estilo')
    } finally { setLoading(false) }
  }

  useEffect(() => { loadPersona() }, [id])

  const handleDelete = async () => {
    if (!persona) return
    try {
      setDeleting(true)
      await PersonaService.deletePersona(persona.id)
      showToast(`Estilo "${persona.name}" excluído com sucesso`, 'success')
      navigate('/personas')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Falha ao excluir estilo', 'error')
    } finally { setDeleting(false) }
  }

  const getLanguageDisplay = (code: string): string => {
    const langs: Record<string, string> = { 'en': 'Inglês', 'pt': 'Português', 'es': 'Espanhol', 'fr': 'Francês', 'de': 'Alemão', 'it': 'Italiano' }
    return langs[code] || code.toUpperCase()
  }

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando estilo de comunicação...</p>
        </div>
      </div>
    )
  }

  if (error || !persona) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-500" />
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Erro ao Carregar</h2>
          <p className="mt-2 text-gray-600">{error || 'Estilo não encontrado'}</p>
          <div className="mt-6 space-x-4">
            <Link to="/personas" className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
              <ArrowLeftIcon className="h-4 w-4 mr-2" />Voltar
            </Link>
            <button onClick={loadPersona} className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
              Tentar Novamente
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Link to="/personas" className="mr-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full" title="Voltar">
                <ArrowLeftIcon className="h-5 w-5" />
              </Link>
              <div>
                <div className="flex items-center">
                  <h1 className="text-3xl font-bold text-gray-900">{persona.name}</h1>
                  {persona.is_default && (
                    <div className="ml-3 flex items-center">
                      <StarIconSolid className="h-6 w-6 text-yellow-400" />
                      <span className="ml-1 text-sm text-yellow-600 font-medium">Padrão</span>
                    </div>
                  )}
                </div>
                <p className="mt-1 text-lg text-gray-600">{persona.title}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Link to={`/personas/${persona.id}/edit`} className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                <PencilIcon className="h-4 w-4 mr-2" />Editar
              </Link>
              <button 
                onClick={() => showConfirm({
                  title: 'Excluir Estilo de Comunicação',
                  message: `Tem certeza de que deseja excluir "${persona.name}"? Esta ação não pode ser desfeita.${persona.is_default ? ' Atenção: Este é o estilo padrão.' : ''}`,
                  isDanger: true,
                  onConfirm: handleDelete
                })} 
                disabled={deleting} 
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:opacity-50"
              >
                <TrashIcon className="h-4 w-4 mr-2" />{deleting ? 'Excluindo...' : 'Excluir'}
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex"><ExclamationTriangleIcon className="h-5 w-5 text-red-400" /><p className="ml-3 text-sm text-red-800">{error}</p></div>
          </div>
        )}

        {/* Detalhes */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Detalhes do Estilo de Comunicação</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">Configuração completa do tom de voz e regras de engajamento.</p>
          </div>
          
          <div className="border-t border-gray-200">
            <dl>
              <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500">Nome</dt>
                <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{persona.name}</dd>
              </div>
              <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500">Título</dt>
                <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{persona.title}</dd>
              </div>
              <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500">Descrição</dt>
                <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2 whitespace-pre-wrap">{persona.description}</dd>
              </div>
              <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500">Idioma dos Comentários</dt>
                <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{getLanguageDisplay(persona.language)}</dd>
              </div>

              <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500">Tom de Voz</dt>
                <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2 whitespace-pre-wrap">{persona.tone_of_voice}</dd>
              </div>
              
              <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500">Princípios</dt>
                <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                  <ul className="list-disc list-inside space-y-1">
                    {persona.principles.map((p, i) => <li key={i}>{p}</li>)}
                  </ul>
                </dd>
              </div>

              {persona.vocabulary_allowed && persona.vocabulary_allowed.length > 0 && (
                <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500">Vocabulário Permitido</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                    <div className="flex flex-wrap gap-2">
                      {persona.vocabulary_allowed.map((w, i) => (
                        <span key={i} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">{w}</span>
                      ))}
                    </div>
                  </dd>
                </div>
              )}
              
              {persona.vocabulary_prohibited && persona.vocabulary_prohibited.length > 0 && (
                <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500">Vocabulário Proibido</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                    <div className="flex flex-wrap gap-2">
                      {persona.vocabulary_prohibited.map((w, i) => (
                        <span key={i} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">{w}</span>
                      ))}
                    </div>
                  </dd>
                </div>
              )}

              {persona.formatting_rules && persona.formatting_rules.length > 0 && (
                <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                  <dt className="text-sm font-medium text-gray-500">Regras de Formatação</dt>
                  <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                    <ul className="list-disc list-inside space-y-1">
                      {persona.formatting_rules.map((r, i) => <li key={i}>{r}</li>)}
                    </ul>
                  </dd>
                </div>
              )}

              <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500">Criado em</dt>
                <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{formatDate(persona.created_at)}</dd>
              </div>
              <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt className="text-sm font-medium text-gray-500">Última Atualização</dt>
                <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{formatDate(persona.updated_at)}</dd>
              </div>
            </dl>
          </div>
        </div>

        {/* Info */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="flex">
            <StarIconOutline className="h-5 w-5 text-blue-400 flex-shrink-0" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">Informações de Uso</h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>Este estilo de comunicação pode ser selecionado ao criar novas campanhas para gerar comentários com o tom e estilo especificados.</p>
                {persona.is_default && (
                  <p className="mt-2 font-medium">Este é o estilo padrão e será selecionado automaticamente para novas campanhas.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  )
}
