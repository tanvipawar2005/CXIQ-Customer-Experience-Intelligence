import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ClerkProvider } from '@clerk/clerk-react'
import App from './App.jsx'
import { CLERK_PUBLISHABLE_KEY, isAuthConfigured } from './services/authConfig.js'
import './index.css'

const clerkAppearance = {
  variables: {
    colorPrimary: '#0F6B5C',
    colorText: '#10151F',
    fontFamily: '"Inter", sans-serif',
    borderRadius: '10px',
  },
}

// Clerk is entirely optional — if no publishable key is configured, CXIQ
// renders normally in guest mode (no ClerkProvider, no Sign In button).
// Adding VITE_CLERK_PUBLISHABLE_KEY to frontend/.env is all that's needed
// to turn login on; no other code changes required.
const root = (
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)

ReactDOM.createRoot(document.getElementById('root')).render(
  isAuthConfigured ? (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY} appearance={clerkAppearance}>
      {root}
    </ClerkProvider>
  ) : (
    root
  )
)
