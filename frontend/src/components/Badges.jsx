const SENTIMENT_STYLES = {
  positive: 'bg-positive-light text-positive',
  neutral: 'bg-neutralx-light text-neutralx',
  negative: 'bg-negative-light text-negative',
}

const PRIORITY_STYLES = {
  Low: 'bg-priority-low/10 text-priority-low',
  Medium: 'bg-priority-medium/10 text-priority-medium',
  High: 'bg-priority-high/10 text-priority-high',
  Critical: 'bg-priority-critical/10 text-priority-critical',
}

const EMOTION_STYLES = {
  Joy: 'bg-gold-light text-gold',
  Love: 'bg-negative-light text-negative',
  Anger: 'bg-priority-critical/10 text-priority-critical',
  Sadness: 'bg-neutralx-light text-ink-soft',
  Fear: 'bg-priority-high/10 text-priority-high',
  Surprise: 'bg-brand-light text-brand-dark',
  Neutral: 'bg-neutralx-light text-neutralx',
}

export function SentimentBadge({ label, className = '' }) {
  const style = SENTIMENT_STYLES[label] || SENTIMENT_STYLES.neutral
  return (
    <span className={`inline-flex items-center rounded-sm px-2.5 py-1 text-xs font-semibold capitalize ${style} ${className}`}>
      {label}
    </span>
  )
}

export function PriorityBadge({ label, className = '' }) {
  const style = PRIORITY_STYLES[label] || PRIORITY_STYLES.Low
  return (
    <span className={`inline-flex items-center rounded-sm px-2.5 py-1 text-xs font-semibold ${style} ${className}`}>
      {label}
    </span>
  )
}

export function EmotionBadge({ label, className = '' }) {
  const style = EMOTION_STYLES[label] || EMOTION_STYLES.Neutral
  return (
    <span className={`inline-flex items-center rounded-sm px-2.5 py-1 text-xs font-semibold ${style} ${className}`}>
      {label}
    </span>
  )
}

export function ConfidencePill({ value }) {
  return (
    <span className="text-xs font-medium text-ink-faint">
      {Math.round(value * 100)}% confidence
    </span>
  )
}
