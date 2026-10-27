import { useCallback, useRef, useState } from 'react'
import { UploadCloud, FileSpreadsheet, CheckCircle2, Download, BarChart3 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { uploadDataset, getDownloadUrl } from '../services/api.js'
import { LoadingState, ErrorState } from './States.jsx'
import DomainSelect from './DomainSelect.jsx'

export default function BatchUpload({ domain, setDomain }) {
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [status, setStatus] = useState('idle') // idle | uploading | done | error
  const [error, setError] = useState('')
  const [summary, setSummary] = useState(null)
  const inputRef = useRef(null)
  const navigate = useNavigate()

  const pickFile = useCallback((f) => {
    if (!f) return
    const okExt = /\.(csv|xlsx|xls)$/i.test(f.name)
    if (!okExt) {
      setError('Please upload a .csv or .xlsx file.')
      setStatus('error')
      return
    }
    setFile(f)
    setStatus('idle')
    setSummary(null)
    setError('')
  }, [])

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    pickFile(e.dataTransfer.files?.[0])
  }

  async function startAnalysis() {
    if (!file) return
    setStatus('uploading')
    setError('')
    try {
      const result = await uploadDataset({ file, domain })
      setSummary(result)
      setStatus('done')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  return (
    <div className="space-y-5">
      <DomainSelect value={domain} onChange={setDomain} className="max-w-xs" />

      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
          dragging ? 'border-brand bg-brand-light' : 'border-surface-border bg-surface-sunken'
        }`}
      >
        <UploadCloud className="h-8 w-8 text-brand" />
        <div>
          <p className="text-sm font-medium text-ink">Drag and drop your CSV or Excel file here</p>
          <p className="mt-1 text-xs text-ink-faint">
            Supported columns: review / text / feedback / comment (required), rating, date, product, category, customer_id (optional)
          </p>
        </div>
        <button
          onClick={() => inputRef.current?.click()}
          className="rounded-md border border-surface-border bg-white px-4 py-2 text-sm font-medium text-ink transition hover:bg-surface-sunken focus-ring"
        >
          Browse files
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          className="hidden"
          onChange={(e) => pickFile(e.target.files?.[0])}
        />
      </div>

      {file && status !== 'uploading' && (
        <div className="flex items-center justify-between rounded-lg border border-surface-border bg-white px-4 py-3">
          <div className="flex items-center gap-3">
            <FileSpreadsheet className="h-5 w-5 text-brand" />
            <div>
              <p className="text-sm font-medium text-ink">{file.name}</p>
              <p className="text-xs text-ink-faint">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          </div>
          {status !== 'done' && (
            <button
              onClick={startAnalysis}
              className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark focus-ring"
            >
              Start Analysis
            </button>
          )}
        </div>
      )}

      {status === 'uploading' && <LoadingState message="Analyzing your dataset — this can take a moment for larger files..." />}

      {status === 'error' && <ErrorState message={error} onRetry={() => setStatus('idle')} />}

      {status === 'done' && summary && (
        <div className="space-y-4 rounded-lg border border-positive/20 bg-positive-light p-5">
          <div className="flex items-center gap-2 text-positive">
            <CheckCircle2 className="h-5 w-5" />
            <p className="font-display text-lg font-semibold">
              {summary.processed_records.toLocaleString()} Reviews Analyzed
            </p>
          </div>
          <p className="text-sm text-ink-soft">
            Detected review column: <strong>{summary.review_column}</strong>
            {summary.skipped_records > 0 && ` · ${summary.skipped_records} row(s) skipped (empty or invalid)`}
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => navigate(`/dashboard?dataset_id=${summary.dataset_id}`)}
              className="inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark focus-ring"
            >
              <BarChart3 className="h-4 w-4" /> View Dashboard
            </button>
            <a
              href={getDownloadUrl(summary.dataset_id)}
              className="inline-flex items-center gap-2 rounded-md border border-surface-border bg-white px-4 py-2 text-sm font-semibold text-ink transition hover:bg-surface-sunken focus-ring"
            >
              <Download className="h-4 w-4" /> Download Results CSV
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
