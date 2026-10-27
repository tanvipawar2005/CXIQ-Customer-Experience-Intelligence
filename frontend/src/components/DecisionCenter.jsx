import { Package, Headset, Radar } from 'lucide-react'
import { PriorityBadge } from './Badges.jsx'

const TEAM_ICONS = {
  'Product Team': Package,
  'Support Team': Headset,
  'CX Team': Radar,
}

export default function DecisionCenter({ data }) {
  if (!data || data.length === 0) {
    return <p className="text-sm text-ink-faint">No urgent decisions flagged right now — CX signals look stable.</p>
  }

  return (
    <div className="space-y-4">
      {data.map((card) => (
        <div key={card.issue} className="hover-card rounded-lg border border-surface-border bg-white p-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h4 className="font-display text-base font-semibold text-ink">{card.issue}</h4>
            <PriorityBadge label={card.level} />
          </div>

          <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-faint">
            {card.evidence.map((e, i) => (
              <li key={i}>• {e}</li>
            ))}
          </ul>

          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
            {Object.entries(card.actions).map(([team, action]) => {
              const Icon = TEAM_ICONS[team] || Package
              return (
                <div key={team} className="rounded-md border border-surface-border bg-surface-sunken p-3">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-ink">
                    <Icon className="h-3.5 w-3.5 text-brand" /> {team}
                  </div>
                  <p className="mt-1 text-xs text-ink-soft">{action}</p>
                </div>
              )
            })}
          </div>

          <p className="mt-3 text-xs italic text-ink-faint">{card.why}</p>
        </div>
      ))}
    </div>
  )
}
