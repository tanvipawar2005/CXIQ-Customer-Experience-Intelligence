import { AlertTriangle, TrendingUp } from 'lucide-react'

const LEVEL_STYLES = {
  Critical: 'border-priority-critical/30 bg-priority-critical/5',
  High: 'border-priority-high/30 bg-priority-high/5',
  Medium: 'border-priority-medium/30 bg-priority-medium/5',
}

const LEVEL_TEXT = {
  Critical: 'text-priority-critical',
  High: 'text-priority-high',
  Medium: 'text-priority-medium',
}

export default function IssueRadar({ data }) {
  if (!data || data.length === 0) {
    return <p className="text-sm text-ink-faint">No significant risk signals detected in the current data.</p>
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {data.map((issue) => (
        <div
          key={issue.aspect}
          className={`hover-card rounded-lg border p-4 ${LEVEL_STYLES[issue.level] || LEVEL_STYLES.Medium}`}
        >
          <div className="flex items-center justify-between">
            <span className={`text-xs font-semibold uppercase tracking-wide ${LEVEL_TEXT[issue.level]}`}>
              {issue.level}
            </span>
            <AlertTriangle className={`h-4 w-4 ${LEVEL_TEXT[issue.level]}`} />
          </div>
          <p className="mt-2 font-display text-base font-semibold text-ink">{issue.aspect}</p>
          <p className="mt-1 text-xs text-ink-faint">
            {issue.mentions} mentions · {issue.negative_pct}% negative
          </p>
          {issue.trend_increase_pp ? (
            <p className={`mt-2 flex items-center gap-1 text-xs font-medium ${LEVEL_TEXT[issue.level]}`}>
              <TrendingUp className="h-3.5 w-3.5" /> +{issue.trend_increase_pp} pts this period
            </p>
          ) : null}
        </div>
      ))}
    </div>
  )
}
