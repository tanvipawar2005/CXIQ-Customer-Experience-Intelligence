import { NavLink, Link } from 'react-router-dom'
import { SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/clerk-react'
import Logo from './Logo.jsx'
import { isAuthConfigured } from '../services/authConfig.js'

const navLinks = [
  { to: '/', label: 'Home', end: true },
  { to: '/analyze', label: 'Analyze' },
  { to: '/dashboard', label: 'Dashboard' },
]

const authedNavLinks = [
  { to: '/my-datasets', label: 'My Datasets' },
]

export default function Navbar() {
  const links = isAuthConfigured ? [...navLinks, ...authedNavLinks] : navLinks
  return (
    <header className="sticky top-0 z-40 border-b border-surface-border bg-surface/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-2.5 focus-ring rounded-sm">
          <Logo size={30} />
          <span className="font-display text-lg font-semibold text-ink">CXIQ</span>
        </Link>
        <div className="flex items-center gap-2">
          <nav className="flex items-center gap-1">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  `rounded-md px-4 py-2 text-sm font-medium transition-colors focus-ring ${
                    isActive
                      ? 'bg-brand-light text-brand-dark'
                      : 'text-ink-soft hover:bg-surface-sunken hover:text-ink'
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
          {isAuthConfigured && (
            <div className="ml-2 flex items-center border-l border-surface-border pl-3">
              <SignedOut>
                <SignInButton mode="modal">
                  <button className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-dark focus-ring">
                    Sign In
                  </button>
                </SignInButton>
              </SignedOut>
              <SignedIn>
                <UserButton afterSignOutUrl="/" />
              </SignedIn>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
