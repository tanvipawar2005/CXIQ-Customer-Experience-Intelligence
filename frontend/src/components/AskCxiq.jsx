import { useState } from 'react'
import { Sparkles, Send, Loader2 } from 'lucide-react'
import { askCxiq } from '../services/api.js'

const SUGGESTED_QUESTIONS = [
  'Why are customers unhappy?',
  'What is our biggest problem?',
  'Which language has the highest negative sentiment?',
  'What should we fix first?',
]

export default function AskCxiq({ datasetId }) {
  const [question, setQuestion] = useState('')
  const [history, setHistory] = useState([]) // {question, answer}
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function ask(q) {
    const finalQuestion = (q || question).trim()
    if (!finalQuestion || loading) return
    setLoading(true)
    setError('')
    try {
      const res = await askCxiq({ datasetId, question: finalQuestion })
      setHistory((prev) => [...prev, { question: finalQuestion, answer: res.answer }])
      setQuestion('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    ask()
  }

  return (
    <div className="space-y-4">
      {history.length === 0 && (
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => ask(q)}
              className="hover-card rounded-full border border-surface-border bg-white px-3 py-1.5 text-xs font-medium text-ink-soft transition hover:border-brand/40 hover:text-brand-dark focus-ring"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {history.length > 0 && (
        <div className="scrollbar-thin max-h-80 space-y-3 overflow-y-auto pr-1">
          {history.map((h, i) => (
            <div key={i} className="space-y-1.5">
              <p className="ml-auto w-fit max-w-[85%] rounded-md rounded-tr-none bg-brand px-3 py-2 text-sm text-white">
                {h.question}
              </p>
              <p className="w-fit max-w-[90%] rounded-md rounded-tl-none border border-surface-border bg-white px-3 py-2 text-sm text-ink-soft">
                {h.answer}
              </p>
            </div>
          ))}
        </div>
      )}

      {error && <p className="text-sm text-negative">{error}</p>}

      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Sparkles className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" />
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask CXIQ about your customer feedback..."
            maxLength={300}
            className="w-full rounded-md border border-surface-border bg-white py-2.5 pl-9 pr-3 text-sm text-ink placeholder:text-ink-faint focus-ring focus:border-brand"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-60 focus-ring"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </button>
      </form>
    </div>
  )
}
