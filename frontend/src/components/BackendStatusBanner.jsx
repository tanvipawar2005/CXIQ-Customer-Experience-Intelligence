import { useEffect, useState } from 'react'
import { WifiOff } from 'lucide-react'
import { checkHealth } from '../services/api.js'

export default function BackendStatusBanner() {
  const [reachable, setReachable] = useState(true)

  useEffect(() => {
    let cancelled = false
    checkHealth()
      .then(() => !cancelled && setReachable(true))
      .catch(() => !cancelled && setReachable(false))
    return () => {
      cancelled = true
    }
  }, [])

  if (reachable) return null

  return (
    <div className="flex items-center justify-center gap-2 bg-negative px-4 py-2 text-center text-xs font-medium text-white">
      <WifiOff className="h-3.5 w-3.5" />
      Can't reach the CXIQ backend at localhost:8000. Start it with{' '}
      <code className="rounded bg-white/20 px-1.5 py-0.5">uvicorn app.main:app --reload</code> from the backend folder.
    </div>
  )
}
