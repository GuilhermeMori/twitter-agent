/**
 * Tweet Comment API Service
 * 
 * Handles all API operations for tweet comments including fetching comments,
 * regeneration, clipboard operations, and statistics with proper TypeScript types.
 */

import api from './api'
import type {
  TweetComment,
  CommentRegenerationRequest,
  CommentStats
} from '../types'

export class TweetCommentService {
  private static readonly BASE_PATH = '/api/campaigns'

  /**
   * Get all comments for a campaign
   */
  static async getCampaignComments(
    campaignId: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<TweetComment[]> {
    try {
      const response = await api.get<TweetComment[]>(
        `${this.BASE_PATH}/${campaignId}/comments`,
        { params: { limit, offset } }
      )
      return response.data
    } catch (error) {
      console.error(`Failed to get comments for campaign ${campaignId}:`, error)
      throw new Error('Failed to load comments. Please try again.')
    }
  }

  /**
   * Get comment for a specific tweet
   */
  static async getTweetComment(
    campaignId: string,
    tweetId: string
  ): Promise<TweetComment> {
    try {
      const response = await api.get<TweetComment>(
        `${this.BASE_PATH}/${campaignId}/tweets/${tweetId}/comment`
      )
      return response.data
    } catch (error) {
      console.error(`Failed to get comment for tweet ${tweetId}:`, error)
      throw new Error('Failed to load comment. Please try again.')
    }
  }

  /**
   * Get comment statistics for a campaign
   */
  static async getCampaignCommentStats(campaignId: string): Promise<CommentStats> {
    try {
      const response = await api.get<CommentStats>(
        `${this.BASE_PATH}/${campaignId}/comments/stats`
      )
      return response.data
    } catch (error) {
      console.error(`Failed to get comment stats for campaign ${campaignId}:`, error)
      throw new Error('Failed to load comment statistics. Please try again.')
    }
  }

  /**
   * Regenerate comment for a tweet
   */
  static async regenerateComment(
    campaignId: string,
    tweetId: string,
    personaId?: string
  ): Promise<TweetComment> {
    try {
      const requestData: CommentRegenerationRequest = {
        campaign_id: campaignId,
        tweet_id: tweetId,
        persona_id: personaId
      }

      const response = await api.post<TweetComment>(
        `${this.BASE_PATH}/${campaignId}/tweets/${tweetId}/regenerate-comment`,
        requestData
      )
      return response.data
    } catch (error) {
      console.error(`Failed to regenerate comment for tweet ${tweetId}:`, error)
      throw new Error('Failed to regenerate comment. Please try again.')
    }
  }

  /**
   * Get comments for specific tweets
   */
  static async getCommentsForTweets(
    campaignId: string,
    tweetIds: string[]
  ): Promise<TweetComment[]> {
    try {
      const tweetIdsParam = tweetIds.join(',')
      const response = await api.get<TweetComment[]>(
        `${this.BASE_PATH}/${campaignId}/tweets/comments`,
        { params: { tweet_ids: tweetIdsParam } }
      )
      return response.data
    } catch (error) {
      console.error(`Failed to get comments for tweets in campaign ${campaignId}:`, error)
      throw new Error('Failed to load comments for tweets. Please try again.')
    }
  }

  /**
   * Copy comment to clipboard
   */
  static async copyToClipboard(commentText: string): Promise<boolean> {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        // Use modern clipboard API
        await navigator.clipboard.writeText(commentText)
        return true
      } else {
        // Fallback for older browsers or non-secure contexts
        return this.fallbackCopyToClipboard(commentText)
      }
    } catch (error) {
      console.error('Failed to copy to clipboard:', error)
      return this.fallbackCopyToClipboard(commentText)
    }
  }

  /**
   * Fallback method for copying to clipboard
   */
  private static fallbackCopyToClipboard(text: string): boolean {
    try {
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      
      const successful = document.execCommand('copy')
      document.body.removeChild(textArea)
      
      return successful
    } catch (error) {
      console.error('Fallback copy failed:', error)
      return false
    }
  }

  /**
   * Get validation status color class
   */
  static getValidationStatusColor(status: 'valid' | 'failed' | 'regenerated'): string {
    switch (status) {
      case 'valid':
        return 'text-green-600'
      case 'failed':
        return 'text-red-600'
      case 'regenerated':
        return 'text-gray-500'
      default:
        return 'text-gray-600'
    }
  }

  /**
   * Get validation status badge color class
   */
  static getValidationStatusBadgeColor(status: 'valid' | 'failed' | 'regenerated'): string {
    switch (status) {
      case 'valid':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'regenerated':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-600'
    }
  }

  /**
   * Get validation status display text
   */
  static getValidationStatusDisplay(status: 'valid' | 'failed' | 'regenerated'): string {
    switch (status) {
      case 'valid':
        return 'Valid'
      case 'failed':
        return 'Failed'
      case 'regenerated':
        return 'Regenerated'
      default:
        return 'Unknown'
    }
  }

  /**
   * Format comment stats for display
   */
  static formatCommentStats(stats: CommentStats) {
    const successRate = stats.total_comments > 0 
      ? ((stats.valid_comments / stats.total_comments) * 100).toFixed(1)
      : '0.0'

    return {
      ...stats,
      success_rate: `${successRate}%`,
      average_char_count_formatted: Math.round(stats.average_char_count).toString()
    }
  }

  /**
   * Format comment for display
   */
  static formatCommentForDisplay(comment: TweetComment) {
    return {
      ...comment,
      validation_status_display: this.getValidationStatusDisplay(comment.validation_status),
      validation_status_color: this.getValidationStatusColor(comment.validation_status),
      validation_status_badge_color: this.getValidationStatusBadgeColor(comment.validation_status),
      created_at_formatted: new Date(comment.created_at).toLocaleDateString(),
      char_count_display: `${comment.char_count}/280`,
      char_count_percentage: (comment.char_count / 280) * 100,
      has_errors: comment.validation_errors && comment.validation_errors.length > 0,
      errors_text: comment.validation_errors?.join(', ') || ''
    }
  }

  /**
   * Validate comment text locally (basic validation)
   */
  static validateCommentText(text: string, tweetAuthor?: string): string[] {
    const errors: string[] = []

    if (!text || !text.trim()) {
      errors.push('Comment cannot be empty')
      return errors
    }

    if (text.length > 280) {
      errors.push(`Comment exceeds 280 characters (${text.length})`)
    }

    if (text.length < 10) {
      errors.push(`Comment too short (${text.length} characters, minimum 10)`)
    }

    if (tweetAuthor && !text.includes(`@${tweetAuthor}`)) {
      errors.push(`Comment must mention @${tweetAuthor}`)
    }

    return errors
  }

  /**
   * Get character count color based on usage
   */
  static getCharCountColor(charCount: number): string {
    const percentage = (charCount / 280) * 100
    
    if (percentage >= 90) return 'text-red-600'
    if (percentage >= 75) return 'text-yellow-600'
    return 'text-gray-600'
  }

  /**
   * Check if comment is ready to copy (valid and not empty)
   */
  static isCommentReadyToCopy(comment: TweetComment): boolean {
    return comment.validation_status === 'valid' && 
           comment.comment_text.trim().length > 0
  }

  /**
   * Extract Twitter username from comment
   */
  static extractTwitterUsername(commentText: string): string | null {
    const match = commentText.match(/@(\w+)/)
    return match ? match[1] : null
  }

  /**
   * Format comment text for Twitter (ensure proper formatting)
   */
  static formatForTwitter(commentText: string): string {
    // Ensure proper spacing and formatting
    return commentText.trim()
  }
}