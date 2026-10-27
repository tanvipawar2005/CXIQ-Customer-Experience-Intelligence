import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Section } from '../components/States.jsx'
import SingleFeedbackForm from '../components/SingleFeedbackForm.jsx'
import BatchUpload from '../components/BatchUpload.jsx'
import CompareLanguages from '../components/CompareLanguages.jsx'

const VALID_MODES = ['single', 'batch', 'compare']

export default function Analyze() {
  const [searchParams] = useSearchParams()
  const requestedMode = searchParams.get('mode')
  const initialMode = VALID_MODES.includes(requestedMode) ? requestedMode : 'single'

  const [mode, setMode] = useState(initialMode) // single | batch | compare
  const [domain, setDomain] = useState('other')

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <div className="mb-8">
        <h1 className="font-display text-2xl font-semibold text-ink sm:text-3xl">Analyze Feedback</h1>
        <p className="mt-2 text-sm text-ink-faint">
          Run a single review through CXIQ's ABSA pipeline, upload a dataset for batch analysis, or compare
          feedback across languages — in English, Hindi, Marathi, Spanish, French or Hinglish.
        </p>
      </div>

      <div className="mb-6 inline-flex rounded-md border border-surface-border bg-white p-1">
        {[
          { key: 'single', label: 'Single Feedback' },
          { key: 'batch', label: 'Upload Dataset' },
          { key: 'compare', label: 'Compare Languages' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setMode(tab.key)}
            className={`rounded-sm px-4 py-2 text-sm font-medium transition-colors focus-ring ${
              mode === tab.key ? 'bg-brand text-white' : 'text-ink-soft hover:bg-surface-sunken'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <Section>
        {mode === 'single' && <SingleFeedbackForm domain={domain} setDomain={setDomain} />}
        {mode === 'batch' && <BatchUpload domain={domain} setDomain={setDomain} />}
        {mode === 'compare' && <CompareLanguages domain={domain} setDomain={setDomain} />}
      </Section>
    </div>
  )
}
