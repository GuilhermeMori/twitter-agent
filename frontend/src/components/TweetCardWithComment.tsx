/**
 * TweetCardWithComment Component
 *
 * Displays a tweet alongside its AI-generated comment and analysis scores.
 * Supports expandable analysis details, copy-to-clipboard, and top-3 badge.
 */

import { useState } from 'react'
import type { Tweet, TweetAnalysis, TweetComment } from '../types'

interface TweetCardWithCommentProps {
  tweet: Tweet
  analysis?: TweetAnalysis
  comment?: TweetComment
  isTop3?: boolean
}

const SCORE_LABELS: Record<string, string> = {
  lead_relevance_score: 'Relevância',
  tone_of_voice_score: 'Tom',
  insight_strength_score: 'Insight',
  engagement_potential_score: 'Engajamento',
  brand_safety_score: 'Brand Safety',
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round((value / 10) * 100)
  const color =
    value >= 7 ? 'bg-green-500' : value >= 4 ? 'bg-yellow-400' : 'bg-red-400'

  return (
    <div className="flex items-center space-x-2 text-xs">
      <span className="w-24 text-gray-500 shrink-0">{label}</span>
      <div className="flex-1 bg-gray-200 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-6 text-right font-medium text-gray-700">{value}</span>
    </div>
  )
}

export default function TweetCardWithComment({
  tweet,
  analysis,
  comment,
  isTop3 = false,
}: TweetCardWithCommentProps) {
  const [showAnalysis, setShowAnalysis] = useState(false)
  const [copied, setCopied] = useState(false)

  const formatNumber = (n: number) => new Intl.NumberFormat('pt-BR').format(n)

  const formatTimestamp = (dateString: string) =>
    new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(dateString))

  const handleCopy = async () => {
    if (!comment?.comment_text) return
    try {
      await navigator.clipboard.writeText(comment.comment_text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      const el = document.createElement('textarea')
      el.value = comment.comment_text
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const verdictColor =
    analysis?.verdict === 'APPROVED'
      ? 'bg-green-100 text-green-800 border-green-200'
      : 'bg-red-100 text-red-800 border-red-200'

  return (
    <div
      className={`border rounded-lg p-5 transition-all hover:shadow-sm ${
        isTop3 ? 'border-yellow-300 bg-yellow-50/30' : 'border-gray-200 bg-white'
      }`}
    >
      {/* Top-3 badge */}
      {isTop3 && (
        <div className="flex items-center space-x-1 mb-3">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800 border border-yellow-300">
            ⭐ Top 3
          </span>
        </div>
      )}

      {/* Tweet header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-gray-900">@{tweet.author}</span>
          <span className="text-gray-400">•</span>
          <span className="text-sm text-gray-500">{formatTimestamp(tweet.timestamp)}</span>
        </div>
        <a
          href={tweet.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-brand-600 hover:text-brand-700 font-medium inline-flex items-center"
        >
          Ver no Twitter
          <svg className="w-3.5 h-3.5 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
            />
          </svg>
        </a>
      </div>

      {/* Tweet text */}
      <p className="text-gray-900 mb-4 whitespace-pre-wrap">{tweet.text}</p>

      {/* Engagement metrics */}
      <div className="flex items-center space-x-5 text-sm text-gray-500 mb-4">
        <span>❤️ {formatNumber(tweet.likes)}</span>
        <span>🔁 {formatNumber(tweet.reposts)}</span>
        <span>💬 {formatNumber(tweet.replies)}</span>
      </div>

      {/* Analysis summary row */}
      {analysis && (
        <div className="flex items-center space-x-3 mb-4">
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${verdictColor}`}
          >
            {analysis.verdict === 'APPROVED' ? '✓ Aprovado' : '✗ Rejeitado'}
          </span>
          <span className="text-sm text-gray-600">
            Score médio:{' '}
            <span className="font-semibold text-gray-900">
              {analysis.average_score.toFixed(1)}
            </span>
            /10
          </span>
          <button
            onClick={() => setShowAnalysis(v => !v)}
            className="text-xs text-brand-600 hover:text-brand-700 font-medium ml-auto"
          >
            {showAnalysis ? 'Ocultar análise ▲' : 'Ver análise ▼'}
          </button>
        </div>
      )}

      {/* Expandable analysis details */}
      {analysis && showAnalysis && (
        <div className="mb-4 bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-2">
          {Object.entries(SCORE_LABELS).map(([key, label]) => (
            <ScoreBar
              key={key}
              label={label}
              value={analysis[key as keyof TweetAnalysis] as number}
            />
          ))}
          {analysis.notes && (
            <p className="text-xs text-gray-600 mt-3 pt-3 border-t border-gray-200">
              <span className="font-medium">Notas:</span> {analysis.notes}
            </p>
          )}
        </div>
      )}

      {/* Generated comment */}
      {comment && (
        <div className="border border-blue-200 bg-blue-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-blue-700 uppercase tracking-wide">
              Comentário gerado
            </span>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-500">{comment.char_count} chars</span>
              <button
                onClick={handleCopy}
                className={`inline-flex items-center px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  copied
                    ? 'bg-green-100 text-green-700 border border-green-200'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                {copied ? (
                  <>
                    <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Copiado!
                  </>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                      />
                    </svg>
                    Copiar
                  </>
                )}
              </button>
            </div>
          </div>
          <p className="text-sm text-gray-900 whitespace-pre-wrap">{comment.comment_text}</p>
          {comment.validation_status === 'regenerated' && (
            <p className="mt-2 text-xs text-amber-600">
              ⚠ Comentário foi regenerado (tentativa {comment.generation_attempt})
            </p>
          )}
        </div>
      )}
    </div>
  )
}
