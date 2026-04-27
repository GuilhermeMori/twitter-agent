// ─── Configuration ───────────────────────────────────────────────────────────

export interface ConfigurationDTO {
  user_email: string
  apify_token: string
  openai_token: string
  smtp_password: string
  twitter_auth_token?: string
  twitter_ct0?: string
}

export interface ConfigurationResponseDTO {
  user_email: string
  apify_token_masked: string
  openai_token_masked: string
  smtp_password_masked: string
  twitter_auth_token_present: boolean
  twitter_ct0_present: boolean
}

// ─── Assistants ───────────────────────────────────────────────────────────────

export type AssistantRole = 'search' | 'comment' | 'review'

export interface Assistant {
  id: string
  name: string
  title: string
  role: AssistantRole
  description: string
  instructions: string
  principles: string[]
  quality_criteria: string[]
  skills: string[]
  is_editable: boolean
  created_at: string
  updated_at: string
}

export interface AssistantUpdateDTO {
  name?: string
  title?: string
  description?: string
  instructions?: string
  principles?: string[]
  quality_criteria?: string[]
  skills?: string[]
}

// ─── Communication Styles ────────────────────────────────────────────────────

export interface CommunicationStyle {
  id: string
  name: string
  title: string
  description: string
  tone_of_voice: string
  principles: string[]
  vocabulary_allowed?: string[]
  vocabulary_prohibited?: string[]
  formatting_rules?: string[]
  language: string
  system_prompt: string
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface CommunicationStyleCreateDTO {
  name: string
  title: string
  description: string
  tone_of_voice: string
  principles: string[]
  vocabulary_allowed?: string[]
  vocabulary_prohibited?: string[]
  formatting_rules?: string[]
  language?: string
  system_prompt: string
  is_default?: boolean
}

export interface CommunicationStyleUpdateDTO {
  name?: string
  title?: string
  description?: string
  tone_of_voice?: string
  principles?: string[]
  vocabulary_allowed?: string[]
  vocabulary_prohibited?: string[]
  formatting_rules?: string[]
  language?: string
  system_prompt?: string
  is_default?: boolean
}

export interface CommunicationStyleSummary {
  id: string
  name: string
  title: string
  language: string
  is_default: boolean
  created_at: string
}

// ─── Legacy Persona types (kept for backward compatibility) ──────────────────

export type Persona = CommunicationStyle
export type PersonaCreateDTO = CommunicationStyleCreateDTO
export type PersonaUpdateDTO = CommunicationStyleUpdateDTO
export type PersonaSummary = CommunicationStyleSummary

// ─── Tweet Analysis ──────────────────────────────────────────────────────────

export type Verdict = 'APPROVED' | 'REJECTED'

export interface TweetAnalysisScores {
  lead_relevance: number
  tone_of_voice: number
  insight_strength: number
  engagement_potential: number
  brand_safety: number
}

export interface TweetAnalysis {
  id: string
  campaign_id: string
  tweet_id: string
  lead_relevance_score: number
  tone_of_voice_score: number
  insight_strength_score: number
  engagement_potential_score: number
  brand_safety_score: number
  average_score: number
  verdict: Verdict
  notes?: string
  is_top_3: boolean
  created_at: string
  updated_at: string
}

export interface TweetAnalysisStats {
  total_tweets: number
  approved_tweets: number
  rejected_tweets: number
  average_score: number
  top_3_count: number
}

// ─── Tweet Comments ──────────────────────────────────────────────────────────

export type ValidationStatus = 'valid' | 'failed' | 'regenerated'

export interface TweetComment {
  id: string
  campaign_id: string
  tweet_id: string
  persona_id: string
  comment_text: string
  char_count: number
  generation_attempt: number
  validation_status: ValidationStatus
  validation_errors?: string[]
  created_at: string
  updated_at: string
}

export interface CommentValidationResult {
  is_valid: boolean
  errors: string[]
  char_count: number
}

export interface CommentRegenerationRequest {
  campaign_id: string
  tweet_id: string
  persona_id?: string
}

export interface CommentStats {
  total_comments: number
  valid_comments: number
  failed_comments: number
  regenerated_comments: number
  average_char_count: number
  max_attempts_used: number
}

// ─── Enhanced Tweet Types ────────────────────────────────────────────────────

export interface TweetWithAnalysis extends Tweet {
  analysis?: TweetAnalysis
}

export interface TweetWithComment extends Tweet {
  comment?: TweetComment
}

export interface TweetWithAnalysisAndComment extends Tweet {
  analysis?: TweetAnalysis
  comment?: TweetComment
}

// ─── Enhanced Campaign Results ───────────────────────────────────────────────

export interface CampaignResultsResponse {
  tweets: TweetWithAnalysisAndComment[]
  total_tweets: number
  analysis_stats: TweetAnalysisStats
  comment_stats: CommentStats
  top_3_tweet_ids: string[]
  has_analysis: boolean
  has_comments: boolean
}

export interface TopTweetResult {
  tweet: Tweet
  analysis: TweetAnalysis
  comment?: TweetComment
}

export interface TopCampaignResultsResponse {
  top_tweets: TopTweetResult[]
  total_top_tweets: number
  campaign_id: string
  campaign_name: string
}

// ─── Campaigns (Updated) ─────────────────────────────────────────────────────

export type SearchType = 'profile' | 'keywords'
export type CampaignStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface CampaignConfig {
  profiles?: string[]
  keywords?: string[]
  language: string
  min_likes: number
  min_retweets: number
  min_replies: number
  days_back: number
}

export interface Campaign {
  id: string
  name: string
  social_network: string
  search_type: SearchType
  config: CampaignConfig
  status: CampaignStatus
  error_message?: string
  document_url?: string
  results_count: number
  persona_id?: string
  communication_style_id?: string
  created_at: string
  updated_at: string
  completed_at?: string
}

export interface CampaignCreateDTO {
  name: string
  social_network?: string
  search_type: SearchType
  profiles?: string
  keywords?: string
  language?: string
  min_likes?: number
  min_retweets?: number
  min_replies?: number
  days_back?: number
  persona_id?: string
  communication_style_id?: string
}

// ─── Tweets ──────────────────────────────────────────────────────────────────

export interface Tweet {
  id: string
  url: string
  author: string
  text: string
  likes: number
  reposts: number
  replies: number
  timestamp: string
}

// ─── Pagination ──────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  total_pages: number
}

// ─── API responses ───────────────────────────────────────────────────────────

export interface CreateCampaignResponse {
  campaign_id: string
}

export interface CreateCommunicationStyleResponse {
  communication_style_id: string
  message: string
}

// Legacy alias
export type CreatePersonaResponse = CreateCommunicationStyleResponse

export interface DownloadResponse {
  download_url: string
}
