const LANGUAGE_FLAGS = {
  English: '🇬🇧', Hindi: '🇮🇳', Marathi: '🇮🇳', Spanish: '🇪🇸', French: '🇫🇷', Hinglish: '🔀',
}

export default function LanguageComparisonTable({ data }) {
  if (!data || data.length === 0) return null

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-surface-border text-left text-xs font-medium uppercase tracking-wide text-ink-faint">
            <th className="py-2 pr-4">Language</th>
            <th className="py-2 pr-4">Reviews</th>
            <th className="py-2 pr-4">Positive</th>
            <th className="py-2 pr-4">Neutral</th>
            <th className="py-2 pr-4">Negative</th>
            <th className="py-2 pr-4">Top Issue</th>
            <th className="py-2 pr-4">CX Score</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => {
            const noReliableData = row.status === 'no_reliable_analyses'
            return (
              <tr key={row.language} className="hover-row border-b border-surface-border last:border-0">
                <td className="py-2.5 pr-4 font-medium text-ink">
                  <span className="mr-1.5">{LANGUAGE_FLAGS[row.language] || '🌐'}</span>
                  {row.language}
                </td>
                <td className="py-2.5 pr-4 text-ink-soft">
                  {row.reviews}
                  {row.unreliable_count > 0 && (
                    <span
                      className="ml-1.5 text-xs font-medium text-gold"
                      title={`${row.unreliable_count} review(s) in ${row.language} could not be translated and are excluded from Positive/Neutral/Negative below.`}
                    >
                      ⚠ {row.unreliable_count} unreliable
                    </span>
                  )}
                </td>
                {noReliableData ? (
                  <td className="py-2.5 pr-4 text-ink-faint italic" colSpan={4}>
                    No reliable analyses — translation failed for every review in this language.
                  </td>
                ) : (
                  <>
                    <td className="py-2.5 pr-4 text-positive">{row.positive_pct}%</td>
                    <td className="py-2.5 pr-4 text-ink-faint">{row.neutral_pct}%</td>
                    <td className="py-2.5 pr-4 text-negative">{row.negative_pct}%</td>
                    <td className="py-2.5 pr-4 text-ink-soft">{row.top_negative_aspect || '—'}</td>
                  </>
                )}
                <td className="py-2.5 pr-4 font-medium text-ink">
                  {noReliableData ? '—' : row.cx_score}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
