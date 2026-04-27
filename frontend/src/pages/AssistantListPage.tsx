/**
 * Assistant List Page
 * 
 * Displays the 3 fixed assistants (Beto, Cadu, Rita) as cards.
 * Users can edit but not create or delete assistants.
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { PencilIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { AssistantService } from '../services/assistantService'
import type { Assistant } from '../types'

export default function AssistantListPage() {
  const navigate = useNavigate()
  const [assistants, setAssistants] = useState<Assistant[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadAssistants()
  }, [])

  const loadAssistants = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await AssistantService.listAssistants()
      setAssistants(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar assistentes')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando assistentes...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Assistentes</h1>
          <p className="mt-2 text-gray-600">
            Os assistentes são agentes de IA que executam tarefas específicas no pipeline.
            Você pode editar suas instruções e princípios, mas não pode criar ou excluir assistentes.
          </p>
        </div>

        {/* Info Banner */}
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            ℹ️ O sistema possui exatamente <strong>3 assistentes fixos</strong>. Cada um é responsável por uma etapa do pipeline:
            busca de posts, geração de comentários e revisão de qualidade.
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              <p className="ml-3 text-sm text-red-800">{error}</p>
            </div>
          </div>
        )}

        {/* Assistant Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {assistants.map((assistant) => {
            const roleColor = AssistantService.getRoleColor(assistant.role)
            const roleIcon = AssistantService.getRoleIcon(assistant.role)
            const roleDisplay = AssistantService.getRoleDisplay(assistant.role)

            return (
              <div
                key={assistant.id}
                className={`bg-white rounded-lg shadow-sm border ${roleColor.border} overflow-hidden hover:shadow-md transition-shadow`}
              >
                {/* Card Header */}
                <div className={`${roleColor.bg} px-6 py-4`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{roleIcon}</span>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">{assistant.name}</h3>
                        <p className="text-sm text-gray-600">{assistant.title}</p>
                      </div>
                    </div>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${roleColor.bg} ${roleColor.text} border ${roleColor.border}`}>
                      {roleDisplay}
                    </span>
                  </div>
                </div>

                {/* Card Body */}
                <div className="px-6 py-4">
                  <p className="text-sm text-gray-600 line-clamp-3 mb-4">
                    {assistant.description}
                  </p>

                  <div className="space-y-2 text-xs text-gray-500">
                    <div className="flex justify-between">
                      <span>Princípios:</span>
                      <span className="font-medium">{assistant.principles.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Critérios de Qualidade:</span>
                      <span className="font-medium">{assistant.quality_criteria.length}</span>
                    </div>
                    {assistant.skills.length > 0 && (
                      <div className="flex justify-between">
                        <span>Habilidades:</span>
                        <span className="font-medium">{assistant.skills.join(', ')}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Footer */}
                <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
                  <button
                    onClick={() => navigate(`/assistants/${assistant.id}/edit`)}
                    className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <PencilIcon className="h-4 w-4 mr-2" />
                    Editar
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
