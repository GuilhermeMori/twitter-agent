/**
 * Assistant API Service
 * 
 * Handles all API operations for assistant management.
 * Assistants are fixed (3 total) and can only be listed and updated.
 */

import api from './api'
import type { Assistant, AssistantUpdateDTO } from '../types'

export class AssistantService {
  private static readonly BASE_PATH = '/api/assistants'

  /**
   * Get all assistants (always returns 3)
   */
  static async listAssistants(): Promise<Assistant[]> {
    try {
      const response = await api.get<{ items: Assistant[]; total: number }>(this.BASE_PATH)
      return response.data.items
    } catch (error) {
      console.error('Falha ao carregar assistentes:', error)
      throw new Error('Falha ao carregar assistentes. Tente novamente.')
    }
  }

  /**
   * Get a specific assistant by ID
   */
  static async getAssistant(assistantId: string): Promise<Assistant> {
    try {
      const response = await api.get<Assistant>(`${this.BASE_PATH}/${assistantId}`)
      return response.data
    } catch (error) {
      console.error(`Falha ao carregar assistente ${assistantId}:`, error)
      throw new Error('Falha ao carregar detalhes do assistente. Tente novamente.')
    }
  }

  /**
   * Update an existing assistant
   */
  static async updateAssistant(
    assistantId: string,
    data: AssistantUpdateDTO
  ): Promise<Assistant> {
    try {
      const response = await api.put<Assistant>(`${this.BASE_PATH}/${assistantId}`, data)
      return response.data
    } catch (error) {
      console.error(`Falha ao atualizar assistente ${assistantId}:`, error)
      throw new Error('Falha ao atualizar assistente. Verifique os dados e tente novamente.')
    }
  }

  /**
   * Get role display name in Portuguese
   */
  static getRoleDisplay(role: string): string {
    const roles: Record<string, string> = {
      'search': 'Busca',
      'comment': 'Comentário',
      'review': 'Revisão'
    }
    return roles[role] || role
  }

  /**
   * Get role icon
   */
  static getRoleIcon(role: string): string {
    const icons: Record<string, string> = {
      'search': '🔍',
      'comment': '✍️',
      'review': '🛡️'
    }
    return icons[role] || '🤖'
  }

  /**
   * Get role color classes
   */
  static getRoleColor(role: string): { bg: string; text: string; border: string } {
    const colors: Record<string, { bg: string; text: string; border: string }> = {
      'search': { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
      'comment': { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
      'review': { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' }
    }
    return colors[role] || { bg: 'bg-gray-50', text: 'text-gray-700', border: 'border-gray-200' }
  }
}
