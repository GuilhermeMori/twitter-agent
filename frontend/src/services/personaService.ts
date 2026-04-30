/**
 * Persona API Service
 * 
 * Handles all API operations for persona management including CRUD operations,
 * pagination, and error handling with proper TypeScript types.
 */

import api from './api'
import type {
  Persona,
  PersonaCreateDTO,
  PersonaUpdateDTO,
  PersonaSummary,
  PaginatedResponse,
  CreatePersonaResponse
} from '../types'

export class PersonaService {
  private static readonly BASE_PATH = '/api/communication-styles'

  /**
   * Create a new persona
   */
  static async createPersona(data: PersonaCreateDTO): Promise<CreatePersonaResponse> {
    try {
      const response = await api.post<CreatePersonaResponse>(this.BASE_PATH, data)
      return response.data
    } catch (error) {
      console.error('Failed to create persona:', error)
      throw new Error('Failed to create persona. Please check your input and try again.')
    }
  }

  /**
   * Get all personas with pagination
   */
  static async listPersonas(
    page: number = 1,
    limit: number = 20
  ): Promise<PaginatedResponse<Persona>> {
    try {
      const response = await api.get<PaginatedResponse<Persona>>(this.BASE_PATH, {
        params: { page, limit }
      })
      return response.data
    } catch (error) {
      console.error('Failed to list personas:', error)
      throw new Error('Failed to load personas. Please try again.')
    }
  }

  /**
   * Get persona summaries for dropdowns and selection lists
   */
  static async listPersonaSummaries(
    page: number = 1,
    limit: number = 50
  ): Promise<PaginatedResponse<PersonaSummary>> {
    try {
      const response = await api.get<PaginatedResponse<PersonaSummary>>(
        `${this.BASE_PATH}/summaries`,
        { params: { page, limit } }
      )
      return response.data
    } catch (error) {
      console.error('Failed to list persona summaries:', error)
      throw new Error('Failed to load persona options. Please try again.')
    }
  }

  /**
   * Get a specific persona by ID
   */
  static async getPersona(personaId: string): Promise<Persona> {
    try {
      const response = await api.get<Persona>(`${this.BASE_PATH}/${personaId}`)
      return response.data
    } catch (error) {
      console.error(`Failed to get persona ${personaId}:`, error)
      throw new Error('Failed to load persona details. Please try again.')
    }
  }

  /**
   * Get the default persona
   */
  static async getDefaultPersona(): Promise<Persona> {
    try {
      const response = await api.get<Persona>(`${this.BASE_PATH}/default`)
      return response.data
    } catch (error) {
      console.error('Failed to get default persona:', error)
      throw new Error('Failed to load default persona. Please try again.')
    }
  }

  /**
   * Update an existing persona
   */
  static async updatePersona(
    personaId: string,
    data: PersonaUpdateDTO
  ): Promise<Persona> {
    try {
      const response = await api.put<Persona>(`${this.BASE_PATH}/${personaId}`, data)
      return response.data
    } catch (error) {
      console.error(`Failed to update persona ${personaId}:`, error)
      throw new Error('Failed to update persona. Please check your input and try again.')
    }
  }

  /**
   * Delete a persona
   */
  static async deletePersona(personaId: string): Promise<void> {
    try {
      await api.delete(`${this.BASE_PATH}/${personaId}`)
    } catch (error: any) {
      console.error(`Failed to delete persona ${personaId}:`, error)
      
      // Handle specific error cases
      if (error.response?.status === 400) {
        const message = error.response.data?.detail || 'Cannot delete persona'
        throw new Error(message)
      }
      
      throw new Error('Failed to delete persona. Please try again.')
    }
  }

  /**
   * Check if a persona name is available (not used by another persona)
   */
  static async isPersonaNameAvailable(
    name: string,
    excludeId?: string
  ): Promise<boolean> {
    try {
      const personas = await this.listPersonas(1, 100) // Get first 100 personas
      
      return !personas.items.some(persona => 
        persona.name.toLowerCase() === name.toLowerCase() && 
        persona.id !== excludeId
      )
    } catch (error) {
      console.error('Failed to check persona name availability:', error)
      return true // Assume available if check fails
    }
  }

  /**
   * Get personas by language
   */
  static async getPersonasByLanguage(language: string): Promise<Persona[]> {
    try {
      const allPersonas = await this.listPersonas(1, 100)
      return allPersonas.items.filter(persona => persona.language === language)
    } catch (error) {
      console.error(`Failed to get personas for language ${language}:`, error)
      throw new Error('Failed to load personas for the specified language.')
    }
  }

  /**
   * Validate persona data before submission
   */
  static validatePersonaData(data: PersonaCreateDTO | PersonaUpdateDTO): string[] {
    const errors: string[] = []

    // Check required fields for create
    if ('name' in data && data.name !== undefined) {
      if (!data.name?.trim()) {
        errors.push('Persona name is required')
      } else if (data.name.length > 255) {
        errors.push('Persona name must be 255 characters or less')
      }
    }

    if ('title' in data && data.title !== undefined) {
      if (!data.title?.trim()) {
        errors.push('Persona title is required')
      } else if (data.title.length > 255) {
        errors.push('Persona title must be 255 characters or less')
      }
    }

    if ('description' in data && data.description !== undefined) {
      if (!data.description?.trim()) {
        errors.push('Persona description is required')
      }
    }

    if ('tone_of_voice' in data && data.tone_of_voice !== undefined) {
      if (!data.tone_of_voice?.trim()) {
        errors.push('Tone of voice is required')
      }
    }

    if ('principles' in data && data.principles !== undefined) {
      if (!data.principles || data.principles.length === 0) {
        errors.push('At least one principle is required')
      } else {
        const validPrinciples = data.principles.filter(p => p.trim())
        if (validPrinciples.length === 0) {
          errors.push('At least one non-empty principle is required')
        }
      }
    }

    // Validate language
    if ('language' in data && data.language !== undefined) {
      const validLanguages = ['en', 'pt', 'es', 'fr', 'de', 'it']
      if (!validLanguages.includes(data.language)) {
        errors.push('Invalid language. Must be one of: ' + validLanguages.join(', '))
      }
    }

    return errors
  }

  /**
   * Format persona data for display
   */
  static formatPersonaForDisplay(persona: Persona) {
    return {
      ...persona,
      principlesText: persona.principles.join('\n• '),
      vocabularyAllowedText: persona.vocabulary_allowed?.join(', ') || 'None specified',
      vocabularyProhibitedText: persona.vocabulary_prohibited?.join(', ') || 'None specified',
      formattingRulesText: persona.formatting_rules?.join('\n• ') || 'None specified',
      languageDisplay: this.getLanguageDisplay(persona.language),
      createdAtFormatted: new Date(persona.created_at).toLocaleDateString(),
      updatedAtFormatted: new Date(persona.updated_at).toLocaleDateString()
    }
  }

  /**
   * Get display name for language code
   */
  private static getLanguageDisplay(languageCode: string): string {
    const languages: Record<string, string> = {
      'en': 'English',
      'pt': 'Portuguese',
      'es': 'Spanish',
      'fr': 'French',
      'de': 'German',
      'it': 'Italian'
    }
    return languages[languageCode] || languageCode.toUpperCase()
  }
}