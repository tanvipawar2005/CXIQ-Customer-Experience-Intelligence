import { useState } from 'react'
import { Sparkles } from 'lucide-react'
import DomainSelect from './DomainSelect.jsx'
import { analyzeFeedback } from '../services/api.js'
import AnalysisResult from './AnalysisResult.jsx'
import { LoadingState, ErrorState } from './States.jsx'

const EXAMPLE = 'The camera is excellent, but the battery drains very quickly and delivery was late.'

export default function SingleFeedbackForm({ domain, setDomain }) {
  const [text, setText] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading | done | error
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!text.trim()) {
      setError('Please enter some customer feedback to analyze.')
      setStatus('error')
      return
    }
    setStatus('loading')
    setError('')
    try {
      const data = await analyzeFeedback({ text, domain })
      setResult(data)
      setStatus('done')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <DomainSelect value={domain} onChange={setDomain} className="max-w-xs" />
        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <label className="text-xs font-medium uppercase tracking-wide text-ink-faint">Customer feedback</label>
            <button
              type="button"
              onClick={() => setText(EXAMPLE)}
              className="text-xs font-medium text-brand hover:underline focus-ring"
            >
              Try an example
            </button>
          </div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
            maxLength={5000}
            placeholder="Paste or type a customer review here..."
            className="w-full resize-none rounded-md border border-surface-border bg-white px-4 py-3 text-sm text-ink placeholder:text-ink-faint focus-ring focus:border-brand"
          />
          <p className="mt-1 text-right text-xs text-ink-faint">{text.length}/5000</p>
        </div>
        <button
          type="submit"
          disabled={status === 'loading'}
          className="inline-flex items-center gap-2 rounded-md bg-brand px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60 focus-ring"
        >
          <Sparkles className="h-4 w-4" /> Analyze Feedback
        </button>
      </form>

      {status === 'loading' && <LoadingState message="Running sentiment, aspect, emotion, and priority analysis..." />}
      {status === 'error' && <ErrorState message={error} />}
      {status === 'done' && result && <AnalysisResult result={result} />}
    </div>
  )
}
