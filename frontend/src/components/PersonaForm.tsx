/**
 * Persona Form Component
 * 
 * Reusable form component for creating and editing personas.
 * Handles validation, field management, and submission.
 */

import React, { useState } from 'react'
import { XMarkIcon, PlusIcon } from '@heroicons/react/24/outline'
import type { PersonaCreateDTO, PersonaUpdateDTO, Persona } from '../types'
import { PersonaService } from '../services/personaService'

interface PersonaFormProps {
  persona?: Persona
  onSubmit: (data: PersonaCreateDTO | PersonaUpdateDTO) => Promise<void>
  onCancel: () => void
  isEdit?: boolean
}

export default function PersonaForm({ persona, onSubmit, onCancel, isEdit = false }: PersonaFormProps) {
  const [formData, setFormData] = useState({
    name: persona?.name || '',
    title: persona?.title || '',
    description: persona?.description || '',
    tone_of_voice: persona?.tone_of_voice || '',
    principles: persona?.principles || [''],
    vocabulary_allowed: persona?.vocabulary_allowed || [],
    vocabulary_prohibited: persona?.vocabulary_prohibited || [],
    formatting_rules: persona?.formatting_rules || [],
    language: persona?.language || 'en',
    system_prompt: persona?.system_prompt || '',
    is_default: persona?.is_default || false
  })

  const [errors, setErrors] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)

  // Temporary input states for array fields
  const [newPrinciple, setNewPrinciple] = useState('')
  const [newVocabAllowed, setNewVocabAllowed] = useState('')
  const [newVocabProhibited, setNewVocabProhibited] = useState('')
  const [newFormattingRule, setNewFormattingRule] = useState('')

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'pt', name: 'Portuguese' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'it', name: 'Italian' }
  ]

  // Handle form field changes
  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    // Clear errors when user starts typing
    if (errors.length > 0) {
      setErrors([])
    }
  }

  // Handle array field additions
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

  const addVocabAllowed = () => {
    if (newVocabAllowed.trim()) {
      setFormData(prev => ({
        ...prev,
        vocabulary_allowed: [...(prev.vocabulary_allowed || []), newVocabAllowed.trim()]
      }))
      setNewVocabAllowed('')
    }
  }

  const removeVocabAllowed = (index: number) => {
    setFormData(prev => ({
      ...prev,
      vocabulary_allowed: prev.vocabulary_allowed?.filter((_, i) => i !== index)
    }))
  }

  const addVocabProhibited = () => {
    if (newVocabProhibited.trim()) {
      setFormData(prev => ({
        ...prev,
        vocabulary_prohibited: [...(prev.vocabulary_prohibited || []), newVocabProhibited.trim()]
      }))
      setNewVocabProhibited('')
    }
  }

  const removeVocabProhibited = (index: number) => {
    setFormData(prev => ({
      ...prev,
      vocabulary_prohibited: prev.vocabulary_prohibited?.filter((_, i) => i !== index)
    }))
  }

  const addFormattingRule = () => {
    if (newFormattingRule.trim()) {
      setFormData(prev => ({
        ...prev,
        formatting_rules: [...(prev.formatting_rules || []), newFormattingRule.trim()]
      }))
      setNewFormattingRule('')
    }
  }

  const removeFormattingRule = (index: number) => {
    setFormData(prev => ({
      ...prev,
      formatting_rules: prev.formatting_rules?.filter((_, i) => i !== index)
    }))
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate form
    const validationErrors = PersonaService.validatePersonaData(formData as PersonaCreateDTO)
    if (validationErrors.length > 0) {
      setErrors(validationErrors)
      return
    }

    try {
      setSubmitting(true)
      setErrors([])
      
      // Filter out empty principles and auto-generate system_prompt
      const principles = formData.principles.filter(p => p.trim())
      const vocabAllowed = formData.vocabulary_allowed?.length ? formData.vocabulary_allowed : undefined
      const vocabProhibited = formData.vocabulary_prohibited?.length ? formData.vocabulary_prohibited : undefined
      const formattingRules = formData.formatting_rules?.length ? formData.formatting_rules : undefined

      // Auto-generate system_prompt from structured fields
      const promptParts: string[] = []
      promptParts.push(`COMMUNICATION STYLE: ${formData.name}`)
      promptParts.push(`ROLE: ${formData.title}`)
      promptParts.push('')
      promptParts.push(`DESCRIPTION:\n${formData.description}`)
      promptParts.push('')
      promptParts.push(`TONE OF VOICE:\n${formData.tone_of_voice}`)
      promptParts.push('')
      promptParts.push(`PRINCIPLES:\n${principles.map(p => `- ${p}`).join('\n')}`)
      if (vocabAllowed?.length) {
        promptParts.push('')
        promptParts.push(`VOCABULARY — ALWAYS USE:\n${vocabAllowed.map(w => `- ${w}`).join('\n')}`)
      }
      if (vocabProhibited?.length) {
        promptParts.push('')
        promptParts.push(`VOCABULARY — NEVER USE:\n${vocabProhibited.map(w => `- ${w}`).join('\n')}`)
      }
      if (formattingRules?.length) {
        promptParts.push('')
        promptParts.push(`FORMATTING RULES:\n${formattingRules.map(r => `- ${r}`).join('\n')}`)
      }
      promptParts.push('')
      promptParts.push(`LANGUAGE: ${formData.language.toUpperCase()}`)

      const cleanedData = {
        ...formData,
        principles,
        vocabulary_allowed: vocabAllowed,
        vocabulary_prohibited: vocabProhibited,
        formatting_rules: formattingRules,
        system_prompt: promptParts.join('\n'),
      }

      await onSubmit(cleanedData)
    } catch (err) {
      setErrors([err instanceof Error ? err.message : 'Failed to save persona'])
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Error Messages */}
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <h3 className="text-sm font-medium text-red-800 mb-2">Por favor, corrija os seguintes erros:</h3>
          <ul className="list-disc list-inside text-sm text-red-700">
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Basic Information */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Informações Básicas</h3>
        
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">
              Nome <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="ex: Parceiro Estratégico"
              required
            />
          </div>

          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700">
              Título <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="title"
              value={formData.title}
              onChange={(e) => handleChange('title', e.target.value)}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="ex: Copywriter de Mídias Sociais"
              required
            />
          </div>
        </div>

        <div className="mt-6">
          <label htmlFor="description" className="block text-sm font-medium text-gray-700">
            Descrição <span className="text-red-500">*</span>
          </label>
          <textarea
            id="description"
            rows={4}
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="Descreva o papel e identidade da persona..."
            required
          />
        </div>

        <div className="mt-6">
          <label htmlFor="tone_of_voice" className="block text-sm font-medium text-gray-700">
            Tom de Voz <span className="text-red-500">*</span>
          </label>
          <textarea
            id="tone_of_voice"
            rows={3}
            value={formData.tone_of_voice}
            onChange={(e) => handleChange('tone_of_voice', e.target.value)}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="Descreva como a persona se comunica..."
            required
          />
        </div>

        <div className="mt-6">
          <label htmlFor="language" className="block text-sm font-medium text-gray-700">
            Idioma <span className="text-red-500">*</span>
          </label>
          <select
            id="language"
            value={formData.language}
            onChange={(e) => handleChange('language', e.target.value)}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            {languages.map(lang => (
              <option key={lang.code} value={lang.code}>{lang.name}</option>
            ))}
          </select>
        </div>

        <div className="mt-6">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={formData.is_default}
              onChange={(e) => handleChange('is_default', e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="ml-2 text-sm text-gray-700">Definir como persona padrão</span>
          </label>
        </div>
      </div>

      {/* Principles */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Princípios <span className="text-red-500">*</span>
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Adicione princípios que orientam como esta persona gera comentários.
        </p>

        <div className="space-y-2 mb-4">
          {formData.principles.filter(p => p.trim()).map((principle, index) => (
            <div key={index} className="flex items-center space-x-2">
              <span className="flex-1 text-sm text-gray-700 bg-gray-50 px-3 py-2 rounded">
                {principle}
              </span>
              <button
                type="button"
                onClick={() => removePrinciple(index)}
                className="text-red-600 hover:text-red-800"
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
            className="flex-1 border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
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

      {/* Vocabulary */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Vocabulário</h3>
        
        {/* Allowed Vocabulary */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Palavras/Frases Permitidas (Opcional)
          </label>
          <div className="space-y-2 mb-4">
            {formData.vocabulary_allowed?.map((word, index) => (
              <div key={index} className="flex items-center space-x-2">
                <span className="flex-1 text-sm text-gray-700 bg-green-50 px-3 py-2 rounded">
                  {word}
                </span>
                <button
                  type="button"
                  onClick={() => removeVocabAllowed(index)}
                  className="text-red-600 hover:text-red-800"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>
            ))}
          </div>
          <div className="flex space-x-2">
            <input
              type="text"
              value={newVocabAllowed}
              onChange={(e) => setNewVocabAllowed(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addVocabAllowed())}
              className="flex-1 border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Adicione palavra/frase permitida..."
            />
            <button
              type="button"
              onClick={addVocabAllowed}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700"
            >
              <PlusIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Prohibited Vocabulary */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Palavras/Frases Proibidas (Opcional)
          </label>
          <div className="space-y-2 mb-4">
            {formData.vocabulary_prohibited?.map((word, index) => (
              <div key={index} className="flex items-center space-x-2">
                <span className="flex-1 text-sm text-gray-700 bg-red-50 px-3 py-2 rounded">
                  {word}
                </span>
                <button
                  type="button"
                  onClick={() => removeVocabProhibited(index)}
                  className="text-red-600 hover:text-red-800"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>
            ))}
          </div>
          <div className="flex space-x-2">
            <input
              type="text"
              value={newVocabProhibited}
              onChange={(e) => setNewVocabProhibited(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addVocabProhibited())}
              className="flex-1 border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Adicione palavra/frase proibida..."
            />
            <button
              type="button"
              onClick={addVocabProhibited}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700"
            >
              <PlusIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Formatting Rules */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Regras de Formatação (Opcional)</h3>
        <p className="text-sm text-gray-600 mb-4">
          Adicione regras específicas de formatação para os comentários gerados.
        </p>

        <div className="space-y-2 mb-4">
          {formData.formatting_rules?.map((rule, index) => (
            <div key={index} className="flex items-center space-x-2">
              <span className="flex-1 text-sm text-gray-700 bg-gray-50 px-3 py-2 rounded">
                {rule}
              </span>
              <button
                type="button"
                onClick={() => removeFormattingRule(index)}
                className="text-red-600 hover:text-red-800"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
          ))}
        </div>

        <div className="flex space-x-2">
          <input
            type="text"
            value={newFormattingRule}
            onChange={(e) => setNewFormattingRule(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addFormattingRule())}
            className="flex-1 border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="ex: Sem emojis, Máximo 280 caracteres..."
          />
          <button
            type="button"
            onClick={addFormattingRule}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <PlusIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Form Actions */}
      <div className="flex justify-end space-x-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {submitting ? 'Salvando...' : isEdit ? 'Atualizar Estilo' : 'Criar Estilo'}
        </button>
      </div>
    </form>
  )
}