/**
 * Persona List Page
 * 
 * Displays a paginated list of personas with actions for create, edit, delete, and view.
 * Shows default persona indicator and provides search/filter functionality.
 */

import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { 
  PlusIcon, 
  PencilIcon, 
  TrashIcon, 
  EyeIcon,
  MagnifyingGlassIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid'
import { PersonaService } from '../services/personaService'
import type { Persona, PaginatedResponse } from '../types'
import { useNotification } from '../contexts/NotificationContext'

export default function PersonaListPage() {
  const navigate = useNavigate()
  const { showToast, showConfirm } = useNotification()
  const [personas, setPersonas] = useState<PaginatedResponse<Persona> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const ITEMS_PER_PAGE = 10

  // Load personas
  const loadPersonas = async (page: number = 1) => {
    try {
      setLoading(true)
      setError(null)
      const response = await PersonaService.listPersonas(page, ITEMS_PER_PAGE)
      setPersonas(response)
      setCurrentPage(page)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load personas')
    } finally {
      setLoading(false)
    }
  }

  // Initial load
  useEffect(() => {
    loadPersonas()
  }, [])

  // Filter personas based on search term
  const filteredPersonas = personas?.items?.filter(persona =>
    persona.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    persona.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    persona.description.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  // Handle delete persona
  const handleDelete = async (personaId: string) => {
    try {
      setDeletingId(personaId)
      await PersonaService.deletePersona(personaId)
      
      // Reload personas
      await loadPersonas(currentPage)
      showToast('Estilo excluído com sucesso!', 'success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete persona')
    } finally {
      setDeletingId(null)
    }
  }

  // Handle page change
  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= (personas?.total_pages || 1)) {
      loadPersonas(page)
    }
  }

  // Get language display name
  const getLanguageDisplay = (languageCode: string): string => {
    const languages: Record<string, string> = {
      'en': 'Inglês',
      'pt': 'Português',
      'es': 'Espanhol',
      'fr': 'Francês',
      'de': 'Alemão',
      'it': 'Italiano'
    }
    return languages[languageCode] || languageCode.toUpperCase()
  }

  if (loading && !personas) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando estilos de comunicação...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Estilos de Comunicação</h1>
              <p className="mt-2 text-gray-600">
                Gerencie os estilos de comunicação que definem o tom de voz dos comentários gerados pela IA.
              </p>
            </div>
            <Link
              to="/personas/create"
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Criar Estilo
            </Link>
          </div>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Buscar estilos por nome, título ou descrição..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Personas List */}
        {personas && (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            {filteredPersonas.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-400 text-lg mb-4">
                  {searchTerm ? 'Nenhum estilo corresponde à sua busca' : 'Nenhum estilo criado ainda'}
                </div>
                {!searchTerm && (
                  <Link
                    to="/personas/create"
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                  >
                    <PlusIcon className="h-5 w-5 mr-2" />
                    Crie Seu Primeiro Estilo
                  </Link>
                )}
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {filteredPersonas.map((persona) => (
                  <li key={persona.id} className="px-6 py-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center">
                          <div className="flex-1">
                            <div className="flex items-center">
                              <h3 className="text-lg font-medium text-gray-900 truncate">
                                {persona.name}
                              </h3>
                              {persona.is_default && (
                                <div className="ml-2 flex items-center">
                                  <StarIconSolid className="h-5 w-5 text-yellow-400" />
                                  <span className="ml-1 text-sm text-yellow-600 font-medium">
                                    Padrão
                                  </span>
                                </div>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mt-1">{persona.title}</p>
                            <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                              {persona.description}
                            </p>
                            <div className="flex items-center mt-2 space-x-4 text-xs text-gray-500">
                              <span>Idioma: {getLanguageDisplay(persona.language)}</span>
                              <span>Princípios: {persona.principles.length}</span>
                              <span>Criado: {new Date(persona.created_at).toLocaleDateString()}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Actions */}
                      <div className="flex items-center space-x-2 ml-4">
                        <button
                          onClick={() => navigate(`/personas/${persona.id}`)}
                          className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full"
                          title="Ver Detalhes"
                        >
                          <EyeIcon className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => navigate(`/personas/${persona.id}/edit`)}
                          className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-full"
                          title="Editar Estilo"
                        >
                          <PencilIcon className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => showConfirm({
                            title: 'Excluir Estilo de Comunicação',
                            message: `Tem certeza de que deseja excluir o estilo "${persona.name}"? Esta ação não pode ser desfeita.`,
                            isDanger: true,
                            onConfirm: () => handleDelete(persona.id)
                          })}
                          disabled={deletingId === persona.id}
                          className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full disabled:opacity-50"
                          title="Excluir Estilo"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {/* Pagination */}
        {personas && personas.total_pages > 1 && (
          <div className="mt-6 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Mostrando {((currentPage - 1) * ITEMS_PER_PAGE) + 1} até{' '}
              {Math.min(currentPage * ITEMS_PER_PAGE, personas.total)} de{' '}
              {personas.total} estilos
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Anterior
              </button>
              {Array.from({ length: personas.total_pages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => handlePageChange(page)}
                  className={`px-3 py-2 border rounded-md text-sm font-medium ${
                    page === currentPage
                      ? 'border-blue-500 bg-blue-50 text-blue-600'
                      : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {page}
                </button>
              ))}
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === personas.total_pages}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Próxima
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}