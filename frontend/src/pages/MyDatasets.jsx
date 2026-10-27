import { useEffect, useState } from 'react'
import { SignedIn, SignedOut, SignInButton } from '@clerk/clerk-react'
import { LogIn } from 'lucide-react'
import { getMyDatasets } from '../services/api.js'
import { isAuthConfigured } from '../services/authConfig.js'
import { LoadingState, ErrorState, EmptyState } from '../components/States.jsx'
import DatasetCard from '../components/DatasetCard.jsx'
import GetStartedActions from '../components/GetStartedActions.jsx'

function PageHeader() {
  return (
    <div className="mb-8">
      <h1 className="font-display text-2xl font-semibold text-ink sm:text-3xl">My Datasets</h1>
      <p className="mt-2 text-sm text-ink-faint">Every dataset you've analyzed, saved to your account.</p>
    </div>
  )
}

function MyDatasetsSignedIn() {
  const [status, setStatus] = useState('loading') // loading | done | error
  const [datasets, setDatasets] = useState([])
  const [error, setError] = useState('')

  function load() {
    setStatus('loading')
    getMyDatasets()
      .then((data) => {
        setDatasets(data || [])
        setStatus('done')
      })
      .catch((err) => {
        setError(err.message)
        setStatus('error')
      })
  }

  useEffect(load, [])

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <PageHeader />

      {status === 'loading' && <LoadingState message="Loading your datasets..." />}

      {status === 'error' && <ErrorState message={error} onRetry={load} />}

      {status === 'done' && datasets.length === 0 && (
        <EmptyState
          title="No datasets yet"
          description="Upload a customer review dataset or try our sample dataset to get started."
          action={<GetStartedActions className="mt-2" />}
        />
      )}

      {status === 'done' && datasets.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {datasets.map((d) => (
            <DatasetCard key={d.dataset_id} dataset={d} />
          ))}
        </div>
      )}
    </div>
  )
}

function MyDatasetsSignedOut() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-16">
      <EmptyState
        title="Sign in to see your dataset history"
        description="My Datasets keeps every dataset you've analyzed, tied to your account, so you can pick up where you left off."
        action={
          <SignInButton mode="modal">
            <button className="mt-2 inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark focus-ring">
              <LogIn className="h-4 w-4" /> Sign In
            </button>
          </SignInButton>
        }
      />
    </div>
  )
}

export default function MyDatasetsPage() {
  if (!isAuthConfigured) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16">
        <EmptyState
          title="My Datasets requires sign-in"
          description="This deployment hasn't configured authentication, so datasets aren't tied to personal accounts. Every analysis is still available directly from the Dashboard."
        />
      </div>
    )
  }
  return (
    <>
      <SignedIn>
        <MyDatasetsSignedIn />
      </SignedIn>
      <SignedOut>
        <MyDatasetsSignedOut />
      </SignedOut>
    </>
  )
}
