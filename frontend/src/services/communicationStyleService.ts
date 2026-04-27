/**
 * Communication Style API Service
 * 
 * Handles all API operations for communication style management including CRUD operations,
 * pagination, and error handling with proper TypeScript types.
 */

import api from './api'
import type {
  CommunicationStyle,
  CommunicationStyleCreateDTO,
  CommunicationStyleUpdateDTO,
  CommunicationStyleSummary,
  PaginatedResponse,
  CreateCommunicationStyleResponse
} from '../types'

export class CommunicationStyleService {
  private static readonly BASE_PATH = '/api/communication-styles'

  /**
   * Create a new communication style
   */
  static async createStyle(data: CommunicationStyleCreateDTO): Promise<CreateCommunicationStyleResponse> {
    try {
      const response = await api.post<CreateCommunicationStyleResponse>(this.BASE_PATH, data)
      return response.data
    } catch (error) {
      console.error('Falha ao criar estilo de comunicação:', error)
      throw new Error('Falha ao criar estilo de comunicação. Verifique os dados e tente novamente.')
    }
  }

  /**
   * Get all communication styles with pagination
   */
  static async listStyles(
    page: number = 1,
    limit: number = 20
  ): Promise<PaginatedResponse<CommunicationStyle>> {
    try {
      const response = await api.get<PaginatedResponse<CommunicationStyle>>(this.BASE_PATH, {
        params: { page, limit }
      })
      return response.data
    } catch (error) {
      console.error('Falha ao carregar estilos de comunicação:', error)
      throw new Error('Falha ao carregar estilos de comunicação. Tente novamente.')
    }
  }

  /**
   * Get communication style summaries for dropdowns
   */
  static async listStyleSummaries(
    page: number = 1,
    limit: number = 50
  ): Promise<PaginatedResponse<CommunicationStyleSummary>> {
    try {
      const response = await api.get<PaginatedResponse<CommunicationStyleSummary>>(
        `${this.BASE_PATH}/summaries`,
        { params: { page, limit } }
      )
      return response.data
    } catch (error) {
      console.error('Falha ao carregar resumos de estilos:', error)
      throw new Error('Falha ao carregar opções de estilos. Tente novamente.')
    }
  }

  /**
   * Get a specific communication style by ID
   */
  static async getStyle(styleId: string): Promise<CommunicationStyle> {
    try {
      const response = await api.get<CommunicationStyle>(`${this.BASE_PATH}/${styleId}`)
      return response.data
    } catch (error) {
      console.error(`Falha ao carregar estilo ${styleId}:`, error)
      throw new Error('Falha ao carregar detalhes do estilo. Tente novamente.')
    }
  }

  /**
   * Get the default communication style
   */
  static async getDefaultStyle(): Promise<CommunicationStyle> {
    try {
      const response = await api.get<CommunicationStyle>(`${this.BASE_PATH}/default`)
      return response.data
    } catch (error) {
      console.error('Falha ao carregar estilo padrão:', error)
      throw new Error('Falha ao carregar estilo padrão. Tente novamente.')
    }
  }

  /**
   * Update an existing communication style
   */
  static async updateStyle(
    styleId: string,
    data: CommunicationStyleUpdateDTO
  ): Promise<CommunicationStyle> {
    try {
      const response = await api.put<CommunicationStyle>(`${this.BASE_PATH}/${styleId}`, data)
      return response.data
    } catch (error) {
      console.error(`Falha ao atualizar estilo ${styleId}:`, error)
      throw new Error('Falha ao atualizar estilo. Verifique os dados e tente novamente.')
    }
  }

  /**
   * Delete a communication style
   */
  static async deleteStyle(styleId: string): Promise<void> {
    try {
      await api.delete(`${this.BASE_PATH}/${styleId}`)
    } catch (error: any) {
      console.error(`Falha ao excluir estilo ${styleId}:`, error)
      
      if (error.response?.status === 400) {
        const message = error.response.data?.detail || 'Não é possível excluir este estilo'
        throw new Error(message)
      }
      
      throw new Error('Falha ao excluir estilo. Tente novamente.')
    }
  }

  /**
   * Validate communication style data before submission
   */
  static validateStyleData(data: CommunicationStyleCreateDTO | CommunicationStyleUpdateDTO): string[] {
    const errors: string[] = []

    if ('name' in data && data.name !== undefined) {
      if (!data.name?.trim()) errors.push('Nome do estilo é obrigatório')
      else if (data.name.length > 255) errors.push('Nome deve ter no máximo 255 caracteres')
    }

    if ('title' in data && data.title !== undefined) {
      if (!data.title?.trim()) errors.push('Título do estilo é obrigatório')
      else if (data.title.length > 255) errors.push('Título deve ter no máximo 255 caracteres')
    }

    if ('description' in data && data.description !== undefined) {
      if (!data.description?.trim()) errors.push('Descrição é obrigatória')
    }

    if ('tone_of_voice' in data && data.tone_of_voice !== undefined) {
      if (!data.tone_of_voice?.trim()) errors.push('Tom de voz é obrigatório')
    }

    if ('principles' in data && data.principles !== undefined) {
      if (!data.principles || data.principles.length === 0) {
        errors.push('Pelo menos um princípio é obrigatório')
      } else {
        const valid = data.principles.filter(p => p.trim())
        if (valid.length === 0) errors.push('Pelo menos um princípio não vazio é obrigatório')
      }
    }

    if ('language' in data && data.language !== undefined) {
      const validLanguages = ['en', 'pt', 'es', 'fr', 'de', 'it']
      if (!validLanguages.includes(data.language)) {
        errors.push('Idioma inválido. Deve ser: ' + validLanguages.join(', '))
      }
    }

    return errors
  }

  /**
   * Get display name for language code
   */
  static getLanguageDisplay(languageCode: string): string {
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
}
