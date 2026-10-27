import { Link } from 'react-router-dom'
import { FileSpreadsheet, Sparkles, ArrowRight } from 'lucide-react'

const DOMAIN_LABELS = {
  electronics: 'Electronics',
  ecommerce: 'E-commerce',
  restaurant: 'Restaurant',
  hotel: 'Hotel',
  travel: 'Travel',
  other: 'Other',
}

function formatDate(iso) {
  if (!iso) return null
  try {
    return new Date(iso).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' })
  } catch {
    return null
  }
}

export default function DatasetCard({ dataset }) {
  const { dataset_id, filename, domain, total_records, created_at, is_sample } = dataset
  const displayName = filename || `Dataset ${dataset_id.slice(0, 8)}`
  const date = formatDate(created_at)

  return (
    <div className="hover-card flex flex-col justify-between rounded-lg border border-surface-border bg-surface-card p-5 shadow-card transition-shadow duration-200 hover:shadow-pop">
      <div>
        <div className="mb-3 flex items-start justify-between gap-2">
          <div className="flex items-start gap-2.5">
            <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-brand-light text-brand-dark">
              <FileSpreadsheet className="h-4 w-4" />
            </span>
            <div>
              <p className="break-all font-display text-sm font-semibold text-ink">{displayName}</p>
              <p className="mt-0.5 text-xs text-ink-faint">
                {(total_records ?? 0).toLocaleString()} reviews
                {domain && ` · ${DOMAIN_LABELS[domain] || domain}`}
              </p>
            </div>
          </div>
          {is_sample && (
            <span className="inline-flex shrink-0 items-center gap-1 rounded-sm bg-gold-light px-2 py-1 text-[11px] font-semibold text-gold">
              <Sparkles className="h-3 w-3" /> Sample
            </span>
          )}
          {!is_sample && (
            <span className="inline-flex shrink-0 items-center rounded-sm bg-positive-light px-2 py-1 text-[11px] font-semibold text-positive">
              Analyzed
            </span>
          )}
        </div>
        {date && <p className="text-xs text-ink-faint">Analyzed: {date}</p>}
      </div>

      <Link
        to={`/dashboard?dataset_id=${dataset_id}`}
        className="mt-4 inline-flex items-center justify-center gap-1.5 rounded-md border border-surface-border bg-white px-3 py-2 text-sm font-medium text-ink transition hover:bg-surface-sunken focus-ring"
      >
        View Analysis <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </div>
  )
}
