import Logo from './Logo.jsx'

export default function Footer() {
  return (
    <footer className="border-t border-surface-border bg-surface-card">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-6 py-8 sm:flex-row">
        <div className="flex items-center gap-2 text-ink-soft">
          <Logo size={20} />
          <span className="text-sm font-medium">CXIQ</span>
        </div>
        <p className="text-xs text-ink-faint">
          AI-Driven Customer Experience Intelligence and Decision Support System — MSc Data Analytics Project.
        </p>
      </div>
    </footer>
  )
}
