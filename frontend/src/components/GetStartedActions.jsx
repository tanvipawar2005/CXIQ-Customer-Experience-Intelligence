import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { UploadCloud, Sparkles, Loader2 } from 'lucide-react'
import { loadSampleDataset } from '../services/api.js'

/**
 * "Upload Dataset" / "Try Sample Dataset" button pair used by every empty
 * state in the new My Datasets / Dashboard experience (spec sections 1 and
 * 10). Loading the sample dataset requires a signed-in user (it's saved to
 * their personal history) — POST /api/datasets/sample handles creating (or
 * reusing) that per-user copy server-side.
 */
export default function GetStartedActions({ className = '' }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleTrySample() {
    setLoading(true)
    setError('')
    try {
      const { dataset_id } = await loadSampleDataset()
      navigate(`/dashboard?dataset_id=${dataset_id}`)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  return (
    <div className={className}>
      <div className="flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={() => navigate('/analyze?mode=batch')}
          className="inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark focus-ring"
        >
          <UploadCloud className="h-4 w-4" /> Upload Dataset
        </button>
        <button
          onClick={handleTrySample}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-md border border-surface-border bg-white px-4 py-2 text-sm font-semibold text-ink transition hover:bg-surface-sunken focus-ring disabled:opacity-60"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          Try Sample Dataset
        </button>
      </div>
      {error && <p className="mt-3 text-center text-xs text-negative">{error}</p>}
    </div>
  )
}
