import { PriorityBadge } from './Badges.jsx'

export default function CustomerVoiceTable({ data }) {
  if (!data || data.length === 0) return null

  const maxMentions = Math.max(...data.map((d) => d.mentions), 1)

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-surface-border text-left text-xs font-medium uppercase tracking-wide text-ink-faint">
            <th className="py-2 pr-4">Aspect</th>
            <th className="py-2 pr-4">Mentions</th>
            <th className="py-2 pr-4">Positive</th>
            <th className="py-2 pr-4">Negative</th>
            <th className="py-2 pr-4">CX Risk</th>
          </tr>
        </thead>
        <tbody>
          {data.slice(0, 8).map((row) => (
            <tr key={row.aspect} className="hover-row border-b border-surface-border last:border-0">
              <td className="py-2.5 pr-4 font-medium text-ink">{row.aspect}</td>
              <td className="py-2.5 pr-4 text-ink-soft">
                <div className="flex items-center gap-2">
                  <div className="h-1.5 w-16 overflow-hidden rounded-full bg-surface-sunken">
                    <div
                      className="h-full rounded-full bg-brand/60"
                      style={{ width: `${Math.max(6, (row.mentions / maxMentions) * 100)}%` }}
                    />
                  </div>
                  <span className="text-xs">{row.mentions}</span>
                </div>
              </td>
              <td className="py-2.5 pr-4 text-positive">{Math.round(row.positive_ratio * 100)}%</td>
              <td className="py-2.5 pr-4 text-negative">
                {row.mentions ? Math.round((row.negative / row.mentions) * 100) : 0}%
              </td>
              <td className="py-2.5 pr-4"><PriorityBadge label={row.risk} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
