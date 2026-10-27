const DOMAINS = [
  { value: 'electronics', label: 'Electronics' },
  { value: 'ecommerce', label: 'E-commerce' },
  { value: 'restaurant', label: 'Restaurant' },
  { value: 'hotel', label: 'Hotel' },
  { value: 'travel', label: 'Travel' },
  { value: 'other', label: 'Other' },
]

export default function DomainSelect({ value, onChange, className = '' }) {
  return (
    <div className={className}>
      <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-ink-faint">
        Industry (optional)
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-surface-border bg-white px-3 py-2.5 text-sm text-ink focus-ring focus:border-brand"
      >
        {DOMAINS.map((d) => (
          <option key={d.value} value={d.value}>
            {d.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export { DOMAINS }
