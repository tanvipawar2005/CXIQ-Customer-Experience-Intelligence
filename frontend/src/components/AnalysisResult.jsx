import { useState } from 'react'
import { ChevronDown, Lightbulb, ListChecks, Languages } from 'lucide-react'
import { SentimentBadge, PriorityBadge, EmotionBadge, ConfidencePill } from './Badges.jsx'

const LANGUAGE_FLAGS = {
  English: '🇬🇧', Hindi: '🇮🇳', Marathi: '🇮🇳', Spanish: '🇪🇸', French: '🇫🇷', Hinglish: '🔀',
}

// =========================================================
// BUSINESS INSIGHT FORMATTING
// =========================================================
//
// Gemini returns business_insight as one plain-text string. It's meant
// to be a short 2-3 sentence narrative (see gemini_service.py's prompt),
// but can still occasionally contain an embedded numbered list (e.g. a
// cached response from before the prompt was tightened, or a model
// slip). Rather than dumping the raw string into one <p> (which reads
// as an unreadable wall of text either way), split it into separate
// lines so it always renders point-wise.
function splitBusinessInsight(text) {
  if (!text) return []

  const splitSentences = (s) =>
    s
      .split(/(?<=[a-z\)\u201d])\.\s+(?=[A-Z])/)
      .map((x) => x.trim())
      .map((x) => (/[.:;!?]$/.test(x) ? x : `${x}.`))
      .filter(Boolean)

  // If it already contains an explicit numbered list ("1. ... 2. ..."),
  // separate the narrative lead-in from the list, split the lead-in into
  // its own sentences, and keep each numbered item as its own line.
  const numberedListPattern = /\s*(?=\d+\.\s)/
  if (/\d+\.\s/.test(text)) {
    const parts = text.split(numberedListPattern).map((s) => s.trim()).filter(Boolean)
    const leadIn = parts[0] && !/^\d+\.\s/.test(parts[0]) ? parts[0] : null
    const listItems = leadIn ? parts.slice(1) : parts
    return [...(leadIn ? splitSentences(leadIn) : []), ...listItems]
  }

  // Otherwise, split into sentences. The lookbehind avoids breaking on
  // decimals/percentages (e.g. "54.83%") by only splitting after a
  // lowercase letter or closing punctuation, never after a digit.
  return splitSentences(text)
}

function TranslationNotice({ detected_language, translated_text, translation_status, original_text }) {
  if (translation_status === 'not_required') return null

  const flag = LANGUAGE_FLAGS[detected_language] || '🌐'
  return (
    <div className="hover-card rounded-lg border border-brand/20 bg-brand-light p-4">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="text-base">{flag}</span>
        <span className="font-medium text-brand-dark">Detected Language: {detected_language}</span>
        <span className="text-ink-faint">·</span>
        {translation_status === 'translated' ? (
          <span className="text-ink-soft">Translated for Analysis: Yes</span>
        ) : (
          <span className="text-ink-soft">Translated for Analysis: No — analyzed original text</span>
        )}
      </div>
      {translation_status === 'translated' && (
        <p className="mt-2 text-sm text-ink-soft">
          <span className="text-xs font-medium uppercase tracking-wide text-ink-faint">Analyzed as: </span>
          "{translated_text}"
        </p>
      )}
    </div>
  )
}

function AspectRow({ aspect }) {
  return (
    <div className="hover-row flex items-center justify-between rounded-md border border-surface-border bg-white px-4 py-3">
      <div>
        <p className="text-sm font-medium text-ink">{aspect.aspect}</p>
        {aspect.mentions?.length > 0 && (
          <p className="text-xs text-ink-faint">mentioned as "{aspect.mentions.join('", "')}"</p>
        )}
      </div>
      <div className="flex items-center gap-3">
        <ConfidencePill value={aspect.confidence} />
        <SentimentBadge label={aspect.sentiment} />
      </div>
    </div>
  )
}

function HighlightedText({ text, words }) {
  if (!words?.length) return <p className="text-sm leading-relaxed text-ink-soft">{text}</p>

  const lookup = {}
  words.forEach((w) => {
    lookup[w.word.toLowerCase()] = w.type
  })

  const parts = text.split(/(\s+)/)
  return (
    <p className="text-sm leading-relaxed text-ink-soft">
      {parts.map((part, i) => {
        const clean = part.toLowerCase().replace(/[^a-z']/g, '')
        const type = lookup[clean]
        if (!type) return <span key={i}>{part}</span>
        const cls =
          type === 'positive'
            ? 'bg-positive-light text-positive'
            : type === 'negative'
            ? 'bg-negative-light text-negative'
            : 'bg-neutralx-light text-ink-soft'
        return (
          <span key={i} className={`rounded px-0.5 font-medium ${cls}`}>
            {part}
          </span>
        )
      })}
    </p>
  )
}

export default function AnalysisResult({ result }) {
  const [showWhy, setShowWhy] = useState(false)
  const {
    overall_sentiment, aspects, emotion, priority, explanation, business_insight,
    recommendations, text, original_text, detected_language, translated_text, translation_status,
  } = result

  return (
    <div className="space-y-5">
      <TranslationNotice
        detected_language={detected_language}
        translated_text={translated_text}
        translation_status={translation_status}
        original_text={original_text}
      />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="hover-card rounded-lg border border-surface-border bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-ink-faint">Overall sentiment</p>
          <div className="mt-2 flex items-center gap-2">
            <SentimentBadge label={overall_sentiment.label} className="text-sm" />
          </div>
          <p className="mt-1.5 text-xs text-ink-faint">{Math.round(overall_sentiment.confidence * 100)}% confidence</p>
        </div>
        <div className="hover-card rounded-lg border border-surface-border bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-ink-faint">Dominant emotion</p>
          <div className="mt-2">
            <EmotionBadge label={emotion.label} className="text-sm" />
          </div>
          <p className="mt-1.5 text-xs text-ink-faint">{Math.round(emotion.confidence * 100)}% confidence</p>
        </div>
        <div className="hover-card rounded-lg border border-surface-border bg-white p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-ink-faint">Complaint priority</p>
          <div className="mt-2">
            <PriorityBadge label={priority.label} className="text-sm" />
          </div>
          <p className="mt-1.5 text-xs text-ink-faint">severity score {priority.score.toFixed(2)}</p>
        </div>
      </div>

      {aspects.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-faint">Aspect-level sentiment</p>
          <div className="space-y-2">
            {aspects.map((a, i) => (
              <AspectRow key={i} aspect={a} />
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-brand/20 bg-brand-light p-4">
          <div className="mb-1.5 flex items-center gap-2 text-brand-dark">
            <Lightbulb className="h-4 w-4" />
            <p className="text-xs font-semibold uppercase tracking-wide">Business insight</p>
          </div>
          <ul className="space-y-1.5 text-sm text-ink-soft">
            {splitBusinessInsight(business_insight).map((line, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-brand-dark">•</span>
                <span>{line}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-lg border border-gold/25 bg-gold-light p-4">
          <div className="mb-1.5 flex items-center gap-2 text-gold">
            <ListChecks className="h-4 w-4" />
            <p className="text-xs font-semibold uppercase tracking-wide">Recommended actions</p>
          </div>
          <ul className="space-y-1 text-sm text-ink-soft">
            {recommendations.map((r, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-gold">{i + 1}.</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="rounded-lg border border-surface-border">
        <button
          onClick={() => setShowWhy((s) => !s)}
          className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-ink focus-ring"
        >
          Why this prediction?
          <ChevronDown className={`h-4 w-4 text-ink-faint transition-transform ${showWhy ? 'rotate-180' : ''}`} />
        </button>
        {showWhy && (
          <div className="space-y-4 border-t border-surface-border px-4 py-4">
            <div>
              <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-faint">Highlighted text</p>
              <HighlightedText text={text} words={explanation.important_words} />
            </div>
            <div>
              <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-faint">Contributing signals</p>
              <ul className="space-y-1 text-sm text-ink-soft">
                {explanation.signals.map((s, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-ink-faint">•</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}