/**
 * Tweet Analysis API Service
 * 
 * Handles all API operations for tweet analysis including fetching analysis data,
 * statistics, and top tweets with proper TypeScript types.
 */

import api from './api'
import type {
  TweetAnalysis,
  TweetAnalysisStats,
  TopCampaignResultsResponse
} from '../types'

export class TweetAnalysisService {
  private static readonly BASE_PATH = '/api/campaigns'

  /**
   * Get all tweet analyses for a campaign
   */
  static async getCampaignAnalysis(
    campaignId: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<TweetAnalysis[]> {
    try {
      const response = await api.get<TweetAnalysis[]>(
        `${this.BASE_PATH}/${campaignId}/analysis`,
        { params: { limit, offset } }
      )
      return response.data
    } catch (error) {
      console.error(`Failed to get analysis for campaign ${campaignId}:`, error)
      throw new Error('Failed to load tweet analysis. Please try again.')
    }
  }

  /**
   * Get top tweets for a campaign
   */
  static async getTopTweets(
    campaignId: string,
    limit: number = 3
  ): Promise<TweetAnalysis[]> {
    try {
      const response = await api.get<TweetAnalysis[]>(
        `${this.BASE_PATH}/${campaignId}/top-tweets`,
        { params: { limit } }
      )
      return response.data
    } catch (error) {
      console.error(`Failed to get top tweets for campaign ${campaignId}:`, error)
      throw new Error('Failed to load top tweets. Please try again.')
    }
  }

  /**
   * Get analysis statistics for a campaign
   */
  static async getCampaignAnalysisStats(campaignId: string): Promise<TweetAnalysisStats> {
    try {
      const response = await api.get<TweetAnalysisStats>(
        `${this.BASE_PATH}/${campaignId}/analysis/stats`
      )
      return response.data
    } catch (error) {
      console.error(`Failed to get analysis stats for campaign ${campaignId}:`, error)
      throw new Error('Failed to load analysis statistics. Please try again.')
    }
  }

  /**
   * Get analysis for a specific tweet
   */
  static async getTweetAnalysis(
    campaignId: string,
    tweetId: string
  ): Promise<TweetAnalysis> {
    try {
      const response = await api.get<TweetAnalysis>(
        `${this.BASE_PATH}/${campaignId}/tweets/${tweetId}/analysis`
      )
      return response.data
    } catch (error) {
      console.error(`Failed to get analysis for tweet ${tweetId}:`, error)
      throw new Error('Failed to load tweet analysis. Please try again.')
    }
  }

  /**
   * Mark top tweets for a campaign
   */
  static async markTopTweets(
    campaignId: string,
    topN: number = 3
  ): Promise<TweetAnalysis[]> {
    try {
      const response = await api.post<TweetAnalysis[]>(
        `${this.BASE_PATH}/${campaignId}/analysis/mark-top-tweets`,
        null,
        { params: { top_n: topN } }
      )
      return response.data
    } catch (error) {
      console.error(`Failed to mark top tweets for campaign ${campaignId}:`, error)
      throw new Error('Failed to mark top tweets. Please try again.')
    }
  }

  /**
   * Get top campaign results with analysis and comments (optimized for email/reporting)
   */
  static async getTopCampaignResults(campaignId: string): Promise<TopCampaignResultsResponse> {
    try {
      const response = await api.get<TopCampaignResultsResponse>(
        `${this.BASE_PATH}/${campaignId}/top-results`
      )
      return response.data
    } catch (error) {
      console.error(`Failed to get top results for campaign ${campaignId}:`, error)
      throw new Error('Failed to load top campaign results. Please try again.')
    }
  }

  /**
   * Calculate score color based on average score
   */
  static getScoreColor(score: number): string {
    if (score >= 8) return 'text-green-600'
    if (score >= 6) return 'text-yellow-600'
    return 'text-red-600'
  }

  /**
   * Get score badge color class
   */
  static getScoreBadgeColor(score: number): string {
    if (score >= 8) return 'bg-green-100 text-green-800'
    if (score >= 6) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  /**
   * Format score for display
   */
  static formatScore(score: number): string {
    return score.toFixed(1)
  }

  /**
   * Get verdict display text
   */
  static getVerdictDisplay(verdict: 'APPROVED' | 'REJECTED'): string {
    return verdict === 'APPROVED' ? 'Approved' : 'Rejected'
  }

  /**
   * Get verdict color class
   */
  static getVerdictColor(verdict: 'APPROVED' | 'REJECTED'): string {
    return verdict === 'APPROVED' ? 'text-green-600' : 'text-red-600'
  }

  /**
   * Get verdict badge color class
   */
  static getVerdictBadgeColor(verdict: 'APPROVED' | 'REJECTED'): string {
    return verdict === 'APPROVED' 
      ? 'bg-green-100 text-green-800' 
      : 'bg-red-100 text-red-800'
  }

  /**
   * Format analysis stats for display
   */
  static formatAnalysisStats(stats: TweetAnalysisStats) {
    const approvalRate = stats.total_tweets > 0 
      ? ((stats.approved_tweets / stats.total_tweets) * 100).toFixed(1)
      : '0.0'

    return {
      ...stats,
      approval_rate: `${approvalRate}%`,
      average_score_formatted: this.formatScore(stats.average_score),
      average_score_color: this.getScoreColor(stats.average_score)
    }
  }

  /**
   * Get criteria display names
   */
  static getCriteriaDisplayNames(): Record<string, string> {
    return {
      lead_relevance_score: 'Lead Relevance',
      tone_of_voice_score: 'Tone of Voice',
      insight_strength_score: 'Insight Strength',
      engagement_potential_score: 'Engagement Potential',
      brand_safety_score: 'Brand Safety'
    }
  }

  /**
   * Get criteria descriptions
   */
  static getCriteriaDescriptions(): Record<string, string> {
    return {
      lead_relevance_score: 'Is the author a relevant decision-maker?',
      tone_of_voice_score: 'Is the tone professional and consultative?',
      insight_strength_score: 'Does the tweet provide valuable insights?',
      engagement_potential_score: 'Does it invite meaningful conversation?',
      brand_safety_score: 'Is it safe for professional brand engagement?'
    }
  }

  /**
   * Format individual analysis for display
   */
  static formatAnalysisForDisplay(analysis: TweetAnalysis) {
    const criteriaNames = this.getCriteriaDisplayNames()
    const criteriaDescriptions = this.getCriteriaDescriptions()

    return {
      ...analysis,
      average_score_formatted: this.formatScore(analysis.average_score),
      average_score_color: this.getScoreColor(analysis.average_score),
      verdict_display: this.getVerdictDisplay(analysis.verdict),
      verdict_color: this.getVerdictColor(analysis.verdict),
      created_at_formatted: new Date(analysis.created_at).toLocaleDateString(),
      criteria: [
        {
          key: 'lead_relevance_score',
          name: criteriaNames.lead_relevance_score,
          description: criteriaDescriptions.lead_relevance_score,
          score: analysis.lead_relevance_score,
          color: this.getScoreColor(analysis.lead_relevance_score)
        },
        {
          key: 'tone_of_voice_score',
          name: criteriaNames.tone_of_voice_score,
          description: criteriaDescriptions.tone_of_voice_score,
          score: analysis.tone_of_voice_score,
          color: this.getScoreColor(analysis.tone_of_voice_score)
        },
        {
          key: 'insight_strength_score',
          name: criteriaNames.insight_strength_score,
          description: criteriaDescriptions.insight_strength_score,
          score: analysis.insight_strength_score,
          color: this.getScoreColor(analysis.insight_strength_score)
        },
        {
          key: 'engagement_potential_score',
          name: criteriaNames.engagement_potential_score,
          description: criteriaDescriptions.engagement_potential_score,
          score: analysis.engagement_potential_score,
          color: this.getScoreColor(analysis.engagement_potential_score)
        },
        {
          key: 'brand_safety_score',
          name: criteriaNames.brand_safety_score,
          description: criteriaDescriptions.brand_safety_score,
          score: analysis.brand_safety_score,
          color: this.getScoreColor(analysis.brand_safety_score)
        }
      ]
    }
  }
}