import { Loader2, Inbox, AlertTriangle } from 'lucide-react'

export function Section({ title, description, action, children, className = '' }) {
  return (
    <section className={`rounded-lg border border-surface-border bg-surface-card p-6 shadow-card transition-shadow duration-200 hover:shadow-pop ${className}`}>
      {(title || action) && (
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            {title && <h3 className="font-display text-lg font-semibold text-ink">{title}</h3>}
            {description && <p className="mt-1 text-sm text-ink-faint">{description}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  )
}

export function LoadingState({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-ink-faint">
      <Loader2 className="h-6 w-6 animate-spin text-brand" />
      <p className="text-sm">{message}</p>
    </div>
  )
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-surface-border bg-surface-sunken py-16 text-center">
      <Inbox className="h-7 w-7 text-ink-faint" />
      <div>
        <p className="font-medium text-ink">{title}</p>
        {description && <p className="mt-1 max-w-sm text-sm text-ink-faint">{description}</p>}
      </div>
      {action}
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-negative/20 bg-negative-light py-12 text-center">
      <AlertTriangle className="h-6 w-6 text-negative" />
      <p className="max-w-md text-sm font-medium text-negative">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-1 rounded-md bg-negative px-4 py-1.5 text-sm font-medium text-white transition hover:opacity-90 focus-ring"
        >
          Try again
        </button>
      )}
    </div>
  )
}
