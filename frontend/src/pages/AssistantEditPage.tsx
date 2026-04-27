/**
 * Assistant Edit Page
 * 
 * Page for editing an assistant's instructions, principles, and quality criteria.
 * Assistants cannot be created or deleted - only edited.
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeftIcon, PlusIcon, XMarkIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { AssistantService } from '../services/assistantService'
import type { Assistant, AssistantUpdateDTO } from '../types'
import { useNotification } from '../contexts/NotificationContext'

export default function AssistantEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { showToast } = useNotification()
  const [assistant, setAssistant] = useState<Assistant | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Form state
  const [name, setName] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [instructions, setInstructions] = useState('')
  const [principles, setPrinciples] = useState<string[]>([])
  const [qualityCriteria, setQualityCriteria] = useState<string[]>([])
  const [skills, setSkills] = useState<string[]>([])

  // Temp inputs
  const [newPrinciple, setNewPrinciple] = useState('')
  const [newCriteria, setNewCriteria] = useState('')
  const [newSkill, setNewSkill] = useState('')

  useEffect(() => {
    if (id) loadAssistant(id)
  }, [id])

  const loadAssistant = async (assistantId: string) => {
    try {
      setLoading(true)
      setError(null)
      const data = await AssistantService.getAssistant(assistantId)
      setAssistant(data)
      setName(data.name)
      setTitle(data.title)
      setDescription(data.description)
      setInstructions(data.instructions)
      setPrinciples([...data.principles])
      setQualityCriteria([...data.quality_criteria])
      setSkills([...data.skills])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar assistente')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!id) return

    // Validate
    const errors: string[] = []
    if (!name.trim()) errors.push('Nome é obrigatório')
    if (!title.trim()) errors.push('Título é obrigatório')
    if (!description.trim()) errors.push('Descrição é obrigatória')
    if (!instructions.trim()) errors.push('Instruções são obrigatórias')
    if (principles.filter(p => p.trim()).length === 0) errors.push('Pelo menos um princípio é obrigatório')

    if (errors.length > 0) {
      setError(errors.join('. '))
      return
    }

    try {
      setSaving(true)
      setError(null)
      setSuccess(null)

      const updateData: AssistantUpdateDTO = {
        name: name.trim(),
        title: title.trim(),
        description: description.trim(),
        instructions: instructions.trim(),
        principles: principles.filter(p => p.trim()),
        quality_criteria: qualityCriteria.filter(c => c.trim()),
        skills: skills.filter(s => s.trim()),
      }

      await AssistantService.updateAssistant(id, updateData)
      showToast('Assistente atualizado com sucesso!', 'success')
      
      setTimeout(() => navigate('/assistants'), 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao salvar assistente')
    } finally {
      setSaving(false)
    }
  }

  // Array helpers
  const addItem = (list: string[], setList: (v: string[]) => void, value: string, setValue: (v: string) => void) => {
    if (value.trim()) {
      setList([...list, value.trim()])
      setValue('')
    }
  }

  const removeItem = (list: string[], setList: (v: string[]) => void, index: number) => {
    setList(list.filter((_, i) => i !== index))
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando assistente...</p>
        </div>
      </div>
    )
  }

  if (!assistant) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Assistente não encontrado.</p>
      </div>
    )
  }

  const roleIcon = AssistantService.getRoleIcon(assistant.role)
  const roleDisplay = AssistantService.getRoleDisplay(assistant.role)
  const roleColor = AssistantService.getRoleColor(assistant.role)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center">
            <Link to="/assistants" className="mr-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full">
              <ArrowLeftIcon className="h-5 w-5" />
            </Link>
            <div className="flex items-center space-x-3">
              <span className="text-2xl">{roleIcon}</span>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Editar {assistant.name}</h1>
                <div className="flex items-center mt-1 space-x-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${roleColor.bg} ${roleColor.text}`}>
                    {roleDisplay}
                  </span>
                  <span className="text-sm text-gray-500">{assistant.title}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4 flex items-center">
            <CheckCircleIcon className="h-5 w-5 text-green-400 mr-3" />
            <p className="text-sm text-green-800">{success}</p>
          </div>
        )}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4 flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mr-3" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Basic Info */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Informações Básicas</h3>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">Nome <span className="text-red-500">*</span></label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Título <span className="text-red-500">*</span></label>
              <input type="text" value={title} onChange={(e) => setTitle(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500" />
            </div>
          </div>
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700">Descrição <span className="text-red-500">*</span></label>
            <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500" />
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Instruções <span className="text-red-500">*</span></h3>
          <p className="text-sm text-gray-500 mb-4">Instruções detalhadas que o assistente segue ao executar suas tarefas.</p>
          <textarea rows={8} value={instructions} onChange={(e) => setInstructions(e.target.value)}
            className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 font-mono text-sm focus:ring-blue-500 focus:border-blue-500" />
        </div>

        {/* Principles */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Princípios <span className="text-red-500">*</span></h3>
          <p className="text-sm text-gray-500 mb-4">Princípios que orientam o comportamento do assistente.</p>
          <div className="space-y-2 mb-4">
            {principles.map((p, i) => (
              <div key={i} className="flex items-center space-x-2">
                <span className="flex-1 text-sm text-gray-700 bg-gray-50 px-3 py-2 rounded">{p}</span>
                <button type="button" onClick={() => removeItem(principles, setPrinciples, i)} className="text-red-600 hover:text-red-800">
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>
            ))}
          </div>
          <div className="flex space-x-2">
            <input type="text" value={newPrinciple} onChange={(e) => setNewPrinciple(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addItem(principles, setPrinciples, newPrinciple, setNewPrinciple))}
              className="flex-1 border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Adicione um princípio..." />
            <button type="button" onClick={() => addItem(principles, setPrinciples, newPrinciple, setNewPrinciple)}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
              <PlusIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Quality Criteria */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Critérios de Qualidade</h3>
          <p className="text-sm text-gray-500 mb-4">Critérios usados para avaliar a qualidade do trabalho do assistente.</p>
          <div className="space-y-2 mb-4">
            {qualityCriteria.map((c, i) => (
              <div key={i} className="flex items-center space-x-2">
                <span className="flex-1 text-sm text-gray-700 bg-gray-50 px-3 py-2 rounded">{c}</span>
                <button type="button" onClick={() => removeItem(qualityCriteria, setQualityCriteria, i)} className="text-red-600 hover:text-red-800">
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>
            ))}
          </div>
          <div className="flex space-x-2">
            <input type="text" value={newCriteria} onChange={(e) => setNewCriteria(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addItem(qualityCriteria, setQualityCriteria, newCriteria, setNewCriteria))}
              className="flex-1 border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Adicione um critério..." />
            <button type="button" onClick={() => addItem(qualityCriteria, setQualityCriteria, newCriteria, setNewCriteria)}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
              <PlusIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Skills */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Habilidades</h3>
          <p className="text-sm text-gray-500 mb-4">Ferramentas e integrações que o assistente pode usar (ex: apify, blotato).</p>
          <div className="space-y-2 mb-4">
            {skills.map((s, i) => (
              <div key={i} className="flex items-center space-x-2">
                <span className="flex-1 text-sm text-gray-700 bg-blue-50 px-3 py-2 rounded">{s}</span>
                <button type="button" onClick={() => removeItem(skills, setSkills, i)} className="text-red-600 hover:text-red-800">
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>
            ))}
          </div>
          <div className="flex space-x-2">
            <input type="text" value={newSkill} onChange={(e) => setNewSkill(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addItem(skills, setSkills, newSkill, setNewSkill))}
              className="flex-1 border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Adicione uma habilidade..." />
            <button type="button" onClick={() => addItem(skills, setSkills, newSkill, setNewSkill)}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
              <PlusIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-4">
          <button type="button" onClick={() => navigate('/assistants')}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
            Cancelar
          </button>
          <button type="button" onClick={handleSave} disabled={saving}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50">
            {saving ? 'Salvando...' : 'Salvar Alterações'}
          </button>
        </div>
      </div>
    </div>
  )
}
