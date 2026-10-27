import { useState } from 'react'
import { Plus, X, Languages, Sparkles } from 'lucide-react'
import DomainSelect from './DomainSelect.jsx'
import { compareLanguages } from '../services/api.js'
import { LoadingState, ErrorState } from './States.jsx'
import { SentimentBadge, PriorityBadge, EmotionBadge } from './Badges.jsx'

const LANGUAGE_FLAGS = {
  English: '🇬🇧', Hindi: '🇮🇳', Marathi: '🇮🇳', Spanish: '🇪🇸', French: '🇫🇷', Hinglish: '🔀',
}

const EXAMPLE_ENTRIES = [
  { label: 'English', text: 'Delivery was fast but customer support was poor.' },
  { label: 'Hindi', text: 'डिलीवरी तेज थी लेकिन कस्टमर सपोर्ट खराब था।' },
  { label: 'Marathi', text: 'डिलिव्हरी जलद होती पण कस्टमर सपोर्ट खराब होता.' },
]

export default function CompareLanguages({ domain, setDomain }) {
  const [entries, setEntries] = useState([
    { label: '', text: '' },
    { label: '', text: '' },
  ])
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')
  const [results, setResults] = useState(null)

  function updateEntry(idx, field, value) {
    setEntries((prev) => prev.map((e, i) => (i === idx ? { ...e, [field]: value } : e)))
  }

  function addEntry() {
    if (entries.length >= 6) return
    setEntries((prev) => [...prev, { label: '', text: '' }])
  }

  function removeEntry(idx) {
    if (entries.length <= 2) return
    setEntries((prev) => prev.filter((_, i) => i !== idx))
  }

  function loadExample() {
    setEntries(EXAMPLE_ENTRIES.map((e) => ({ ...e })))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const valid = entries.filter((en) => en.text.trim())
    if (valid.length < 2) {
      setError('Please enter at least two feedback entries to compare.')
      setStatus('error')
      return
    }
    setStatus('loading')
    setError('')
    try {
      const data = await compareLanguages({
        entries: valid.map((en) => ({ text: en.text, label: en.label || undefined })),
        domain,
      })
      setResults(data)
      setStatus('done')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-ink-faint">
            Enter the same (or similar) customer feedback in different languages to see how CXIQ understands
            customer experience consistently across markets.
          </p>
        </div>
        <button
          type="button"
          onClick={loadExample}
          className="shrink-0 text-xs font-medium text-brand hover:underline focus-ring"
        >
          Load example
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <DomainSelect value={domain} onChange={setDomain} className="max-w-xs" />

        <div className="space-y-3">
          {entries.map((entry, idx) => (
            <div key={idx} className="hover-card flex gap-2 rounded-lg border border-surface-border bg-white p-3">
              <input
                type="text"
                value={entry.label}
                onChange={(e) => updateEntry(idx, 'label', e.target.value)}
                placeholder="Label (optional)"
                className="w-32 shrink-0 rounded-md border border-surface-border bg-white px-2.5 py-2 text-sm text-ink placeholder:text-ink-faint focus-ring focus:border-brand"
              />
              <textarea
                value={entry.text}
                onChange={(e) => updateEntry(idx, 'text', e.target.value)}
                rows={2}
                maxLength={2000}
                placeholder="Enter feedback in any supported language..."
                className="flex-1 resize-none rounded-md border border-surface-border bg-white px-3 py-2 text-sm text-ink placeholder:text-ink-faint focus-ring focus:border-brand"
              />
              {entries.length > 2 && (
                <button
                  type="button"
                  onClick={() => removeEntry(idx)}
                  className="self-start rounded-md p-1.5 text-ink-faint transition hover:bg-negative-light hover:text-negative focus-ring"
                  aria-label="Remove entry"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
        </div>

        <div className="flex items-center gap-3">
          {entries.length < 6 && (
            <button
              type="button"
              onClick={addEntry}
              className="inline-flex items-center gap-1.5 rounded-md border border-surface-border bg-white px-3 py-1.5 text-xs font-medium text-ink transition hover:bg-surface-sunken focus-ring"
            >
              <Plus className="h-3.5 w-3.5" /> Add entry
            </button>
          )}
          <button
            type="submit"
            disabled={status === 'loading'}
            className="inline-flex items-center gap-2 rounded-md bg-brand px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60 focus-ring"
          >
            <Languages className="h-4 w-4" /> Compare
          </button>
        </div>
      </form>

      {status === 'loading' && <LoadingState message="Analyzing each language entry..." />}
      {status === 'error' && <ErrorState message={error} />}

      {status === 'done' && results && (
        <div className="overflow-x-auto rounded-lg border border-surface-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border bg-surface-sunken text-left text-xs font-medium uppercase tracking-wide text-ink-faint">
                <th className="px-4 py-3">Language</th>
                <th className="px-4 py-3">Sentiment</th>
                <th className="px-4 py-3">Emotion</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">CX Score</th>
                <th className="px-4 py-3">Main Aspect</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i} className="hover-row border-b border-surface-border last:border-0">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span>{LANGUAGE_FLAGS[r.detected_language] || '🌐'}</span>
                      <div>
                        <p className="font-medium text-ink">{r.label || r.detected_language}</p>
                        <p className="max-w-xs truncate text-xs text-ink-faint" title={r.original_text}>
                          {r.original_text}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3"><SentimentBadge label={r.overall_sentiment} /></td>
                  <td className="px-4 py-3"><EmotionBadge label={r.emotion} /></td>
                  <td className="px-4 py-3"><PriorityBadge label={r.priority} /></td>
                  <td className="px-4 py-3 font-medium text-ink">{r.cx_score}/100</td>
                  <td className="px-4 py-3 text-ink-soft">{r.main_aspect || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
