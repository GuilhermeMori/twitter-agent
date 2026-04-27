import { useState, useEffect } from 'react'
import api from '../services/api'
import type { ConfigurationDTO, ConfigurationResponseDTO } from '../types'

export default function ConfigurationPage() {
  // Form state
  const [formData, setFormData] = useState<ConfigurationDTO>({
    user_email: '',
    apify_token: '',
    openai_token: '',
    smtp_password: '',
  })

  // UI state
  const [loading, setLoading] = useState(false)
  const [loadingConfig, setLoadingConfig] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  // Load existing configuration on mount
  useEffect(() => {
    loadConfiguration()
  }, [])

  const loadConfiguration = async () => {
    try {
      setLoadingConfig(true)
      setError(null)
      const response = await api.get<ConfigurationResponseDTO>('/api/configuration')
      
      // Populate form with existing data (masked tokens)
      setFormData({
        user_email: response.data.user_email,
        apify_token: response.data.apify_token_masked,
        openai_token: response.data.openai_token_masked,
        smtp_password: response.data.smtp_password_masked,
      })
    } catch (err) {
      // If no configuration exists yet, that's okay - user will create one
      if (err instanceof Error && err.message.includes('404')) {
        setError(null)
      } else {
        setError(err instanceof Error ? err.message : 'Erro ao carregar configurações')
      }
    } finally {
      setLoadingConfig(false)
    }
  }

  const handleInputChange = (field: keyof ConfigurationDTO, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    // Clear validation error for this field when user starts typing
    if (validationErrors[field]) {
      setValidationErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
    // Clear success message when user modifies form
    if (success) {
      setSuccess(false)
    }
  }

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}

    // Email validation
    if (!formData.user_email.trim()) {
      errors.user_email = 'Email é obrigatório'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.user_email)) {
      errors.user_email = 'Email inválido'
    }

    // Apify token validation
    if (!formData.apify_token.trim()) {
      errors.apify_token = 'Token da API do Apify é obrigatório'
    }

    // OpenAI token validation
    if (!formData.openai_token.trim()) {
      errors.openai_token = 'Token da API da OpenAI é obrigatório'
    }

    // SMTP password validation
    if (!formData.smtp_password.trim()) {
      errors.smtp_password = 'Senha SMTP é obrigatória'
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Clear previous messages
    setError(null)
    setSuccess(false)

    // Validate form
    if (!validateForm()) {
      return
    }

    try {
      setLoading(true)
      await api.post('/api/configuration', formData)
      setSuccess(true)
      // Reload configuration to get masked tokens
      await loadConfiguration()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar configurações')
    } finally {
      setLoading(false)
    }
  }

  if (loadingConfig) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
          <p className="mt-4 text-gray-600">Carregando configurações...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Configurações</h1>
          <p className="mt-2 text-gray-600">
            Gerencie suas credenciais de API e configurações de email.
          </p>
        </div>

        {/* Success Message */}
        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4 flex items-start">
            <svg
              className="w-5 h-5 text-green-600 mt-0.5 mr-3 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <h3 className="text-sm font-medium text-green-800">
                Configurações salvas com sucesso!
              </h3>
              <p className="mt-1 text-sm text-green-700">
                Suas credenciais foram armazenadas de forma segura.
              </p>
            </div>
          </div>
        )}

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
              <h3 className="text-sm font-medium text-red-800">Erro ao salvar configurações</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Configuration Form */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200">
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={formData.user_email}
                onChange={(e) => handleInputChange('user_email', e.target.value)}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors ${
                  validationErrors.user_email
                    ? 'border-red-300 bg-red-50'
                    : 'border-gray-300 bg-white'
                }`}
                placeholder="seu-email@exemplo.com"
                disabled={loading}
              />
              {validationErrors.user_email && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.user_email}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Email usado para receber notificações de campanhas concluídas
              </p>
            </div>

            {/* Apify Token Field */}
            <div>
              <label htmlFor="apify_token" className="block text-sm font-medium text-gray-700 mb-2">
                Token da API do Apify
              </label>
              <input
                id="apify_token"
                type="password"
                value={formData.apify_token}
                onChange={(e) => handleInputChange('apify_token', e.target.value)}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors font-mono text-sm ${
                  validationErrors.apify_token
                    ? 'border-red-300 bg-red-50'
                    : 'border-gray-300 bg-white'
                }`}
                placeholder="apify_api_..."
                disabled={loading}
              />
              {validationErrors.apify_token && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.apify_token}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Token de autenticação para o serviço de scraping do Apify
              </p>
            </div>

            {/* OpenAI Token Field */}
            <div>
              <label htmlFor="openai_token" className="block text-sm font-medium text-gray-700 mb-2">
                Token da API da OpenAI
              </label>
              <input
                id="openai_token"
                type="password"
                value={formData.openai_token}
                onChange={(e) => handleInputChange('openai_token', e.target.value)}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors font-mono text-sm ${
                  validationErrors.openai_token
                    ? 'border-red-300 bg-red-50'
                    : 'border-gray-300 bg-white'
                }`}
                placeholder="sk-..."
                disabled={loading}
              />
              {validationErrors.openai_token && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.openai_token}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Token de autenticação para análise de conteúdo com OpenAI
              </p>
            </div>

            {/* SMTP Password Field */}
            <div>
              <label htmlFor="smtp_password" className="block text-sm font-medium text-gray-700 mb-2">
                Senha SMTP do Gmail
              </label>
              <input
                id="smtp_password"
                type="password"
                value={formData.smtp_password}
                onChange={(e) => handleInputChange('smtp_password', e.target.value)}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors ${
                  validationErrors.smtp_password
                    ? 'border-red-300 bg-red-50'
                    : 'border-gray-300 bg-white'
                }`}
                placeholder="••••••••"
                disabled={loading}
              />
              {validationErrors.smtp_password && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.smtp_password}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Senha de aplicativo do Gmail para envio de emails
              </p>
            </div>

            {/* Security Notice */}
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
                <h3 className="text-sm font-medium text-blue-800">Segurança</h3>
                <p className="mt-1 text-sm text-blue-700">
                  Suas credenciais são armazenadas de forma criptografada e nunca são expostas
                  completamente nas respostas da API.
                </p>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex items-center justify-end space-x-4 pt-4 border-t border-gray-200">
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
                    <span>Salvando...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    <span>Salvar Configurações</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Help Section */}
        <div className="mt-8 bg-white shadow-sm rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Como obter suas credenciais</h2>
          <div className="space-y-4 text-sm text-gray-600">
            <div>
              <h3 className="font-medium text-gray-900 mb-1">Token do Apify</h3>
              <p>
                Acesse{' '}
                <a
                  href="https://console.apify.com/account/integrations"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand-600 hover:text-brand-700 underline"
                >
                  console.apify.com/account/integrations
                </a>{' '}
                e copie seu token de API pessoal.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-1">Token da OpenAI</h3>
              <p>
                Acesse{' '}
                <a
                  href="https://platform.openai.com/api-keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand-600 hover:text-brand-700 underline"
                >
                  platform.openai.com/api-keys
                </a>{' '}
                e crie uma nova chave de API.
              </p>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-1">Senha SMTP do Gmail</h3>
              <p>
                Acesse{' '}
                <a
                  href="https://myaccount.google.com/apppasswords"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand-600 hover:text-brand-700 underline"
                >
                  myaccount.google.com/apppasswords
                </a>{' '}
                e gere uma senha de aplicativo para "Mail".
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
