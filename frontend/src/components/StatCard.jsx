export default function StatCard({ label, value, sub, accent = 'ink' }) {
  const accentClass = {
    ink: 'text-ink',
    positive: 'text-positive',
    negative: 'text-negative',
    brand: 'text-brand',
    gold: 'text-gold',
  }[accent]

  return (
    <div className="rounded-lg border border-surface-border bg-surface-card p-5 shadow-card transition-all duration-200 hover:-translate-y-0.5 hover:shadow-pop hover:border-brand/30">
      <p className="text-xs font-medium uppercase tracking-wide text-ink-faint">{label}</p>
      <p className={`mt-2 font-display text-3xl font-semibold ${accentClass}`}>{value}</p>
      {sub && <p className="mt-1 text-xs text-ink-faint">{sub}</p>}
    </div>
  )
}
