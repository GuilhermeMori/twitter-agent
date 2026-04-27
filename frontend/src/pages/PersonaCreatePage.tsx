/**
 * Persona Create Page (Criar Estilo de Comunicação)
 */

import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'
import PersonaForm from '../components/PersonaForm'
import { PersonaService } from '../services/personaService'
import type { PersonaCreateDTO, PersonaUpdateDTO } from '../types'
import { useNotification } from '../contexts/NotificationContext'

export default function PersonaCreatePage() {
  const navigate = useNavigate()
  const { showToast } = useNotification()
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (data: PersonaCreateDTO | PersonaUpdateDTO) => {
    try {
      setError(null)
      const response = await PersonaService.createPersona(data as PersonaCreateDTO)
      showToast('Estilo de comunicação criado com sucesso!', 'success')
      navigate(`/personas/${response.communication_style_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao criar estilo de comunicação')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="flex items-center">
            <Link to="/personas" className="mr-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full" title="Voltar">
              <ArrowLeftIcon className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Criar Estilo de Comunicação</h1>
              <p className="mt-1 text-sm text-gray-600">Defina um novo tom de voz para gerar comentários em tweets</p>
            </div>
          </div>
        </div>

        <PersonaForm onSubmit={handleSubmit} onCancel={() => navigate('/personas')} />

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}
      </div>
    </div>
  )
}
