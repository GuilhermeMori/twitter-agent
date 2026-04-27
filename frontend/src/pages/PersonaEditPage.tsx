/**
 * Persona Edit Page (Editar Estilo de Comunicação)
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeftIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import PersonaForm from '../components/PersonaForm'
import { PersonaService } from '../services/personaService'
import type { Persona, PersonaUpdateDTO } from '../types'
import { useNotification } from '../contexts/NotificationContext'

export default function PersonaEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { showToast } = useNotification()
  
  const [persona, setPersona] = useState<Persona | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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

  const handleSubmit = async (data: PersonaUpdateDTO) => {
    if (!id) return
    try {
      setError(null)
      const updated = await PersonaService.updatePersona(id, data)
      showToast(`Estilo "${updated.name}" atualizado com sucesso`, 'success')
      navigate(`/personas/${updated.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao atualizar estilo')
    }
  }

  const handleCancel = () => { navigate(id ? `/personas/${id}` : '/personas') }

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

  if (error && !persona) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-500" />
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Erro ao Carregar</h2>
          <p className="mt-2 text-gray-600">{error}</p>
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

  if (!persona) return null

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="flex items-center">
            <Link to={`/personas/${id}`} className="mr-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full" title="Voltar">
              <ArrowLeftIcon className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Editar Estilo de Comunicação</h1>
              <p className="mt-1 text-sm text-gray-600">Atualizando "{persona.name}"</p>
            </div>
          </div>
        </div>

        <PersonaForm persona={persona} onSubmit={handleSubmit} onCancel={handleCancel} isEdit={true} />

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}
      </div>
    </div>
  )
}
