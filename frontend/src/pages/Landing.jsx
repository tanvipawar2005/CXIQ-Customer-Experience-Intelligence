import { Link } from 'react-router-dom'
import {
  ArrowRight, BarChart3, Smile, Flame, TrendingUp, Sparkles, ShieldCheck,
  Camera, BatteryLow, Truck, Store, Cpu, UtensilsCrossed, Hotel, Headset,
} from 'lucide-react'
import { SentimentBadge } from '../components/Badges.jsx'

const capabilities = [
  { icon: BarChart3, title: 'Sentiment Intelligence', desc: 'ML-driven positive / neutral / negative classification with confidence scoring on every prediction.' },
  { icon: Sparkles, title: 'Aspect-Based Analysis', desc: 'Identify exactly what customers are talking about — battery, delivery, service — and how they feel about each.' },
  { icon: Smile, title: 'Emotion Detection', desc: 'Go beyond polarity to detect joy, love, anger, sadness, fear, and surprise in customer language.' },
  { icon: Flame, title: 'Complaint Intelligence', desc: 'Explainable Low / Medium / High / Critical priority scoring so urgent issues never get buried.' },
  { icon: TrendingUp, title: 'Trend Detection', desc: 'Track sentiment and issue trends over time and catch emerging problems before they escalate.' },
  { icon: ShieldCheck, title: 'AI Recommendations', desc: 'Grounded, structured business insights and next-step actions — never generic filler.' },
]

const benefits = [
  { icon: Cpu, title: 'Electronics', desc: 'Track battery, camera, and performance sentiment across product generations.' },
  { icon: Store, title: 'E-commerce', desc: 'Separate delivery and packaging friction from genuine product quality issues.' },
  { icon: UtensilsCrossed, title: 'Restaurants', desc: 'Understand whether complaints are about food, service, or ambience.' },
  { icon: Hotel, title: 'Hotels', desc: 'Monitor room cleanliness, staff service, and pricing sentiment by property.' },
  { icon: Headset, title: 'Support Teams', desc: 'Prioritize tickets automatically using explainable complaint severity scoring.' },
]

export default function Landing() {
  return (
    <div>
      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 pb-20 pt-16 sm:pt-24">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <span className="inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand-light px-3 py-1 text-xs font-semibold text-brand-dark">
              AI-Driven Customer Experience Intelligence
            </span>
            <h1 className="mt-5 font-display text-4xl font-semibold leading-tight text-ink sm:text-5xl">
              Understand What Your Customers Really Think.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-ink-faint">
              CXIQ uses aspect-based sentiment analysis, emotion detection, and AI-powered recommendations
              to transform unstructured customer feedback into actionable business decisions — turning
              "customers are unhappy" into exactly why, where, and what to do about it.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/analyze"
                className="inline-flex items-center gap-2 rounded-md bg-brand px-5 py-3 text-sm font-semibold text-white shadow-pop transition hover:bg-brand-dark focus-ring"
              >
                Analyze Feedback <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 rounded-md border border-surface-border bg-white px-5 py-3 text-sm font-semibold text-ink transition hover:bg-surface-sunken focus-ring"
              >
                Explore Dashboard
              </Link>
            </div>
          </div>

          <div className="lg:col-span-5">
            <div className="rounded-lg border border-surface-border bg-surface-card p-5 shadow-pop">
              <p className="text-xs font-medium uppercase tracking-wide text-ink-faint">Live example</p>
              <p className="mt-2 rounded-md bg-surface-sunken p-3 text-sm text-ink-soft">
                "The camera is excellent, but the battery drains very quickly and delivery was late."
              </p>
              <div className="mt-4 space-y-2">
                {[
                  { aspect: 'Camera', sentiment: 'positive', icon: Camera },
                  { aspect: 'Battery', sentiment: 'negative', icon: BatteryLow },
                  { aspect: 'Delivery', sentiment: 'negative', icon: Truck },
                ].map((row) => (
                  <div key={row.aspect} className="flex items-center justify-between rounded-md border border-surface-border px-3 py-2">
                    <span className="flex items-center gap-2 text-sm font-medium text-ink">
                      <row.icon className="h-4 w-4 text-ink-faint" /> {row.aspect}
                    </span>
                    <SentimentBadge label={row.sentiment} />
                  </div>
                ))}
              </div>
              <div className="mt-4 rounded-md bg-brand-light p-3 text-xs text-brand-dark">
                Overall sentiment: <strong>Negative</strong> · Priority: <strong>Medium</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-y border-surface-border bg-surface-sunken py-16">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center font-display text-2xl font-semibold text-ink">How It Works</h2>
          <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {['Feedback', 'AI Analysis', 'Customer Intelligence', 'Business Action'].map((step, i) => (
              <div key={step} className="relative rounded-lg border border-surface-border bg-white p-5">
                <span className="font-display text-2xl font-semibold text-brand/30">0{i + 1}</span>
                <p className="mt-2 font-medium text-ink">{step}</p>
                {i < 3 && (
                  <ArrowRight className="absolute -right-3 top-1/2 hidden h-5 w-5 -translate-y-1/2 text-ink-faint sm:block lg:right-[-22px]" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Core capabilities */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="font-display text-2xl font-semibold text-ink">Core Capabilities</h2>
        <p className="mt-2 max-w-2xl text-sm text-ink-faint">
          A single, focused pipeline — not a scattered collection of demos.
        </p>
        <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {capabilities.map((cap) => (
            <div key={cap.title} className="hover-card rounded-lg border border-surface-border bg-surface-card p-5 shadow-card">
              <div className="mb-3 inline-flex rounded-md bg-brand-light p-2.5 text-brand-dark">
                <cap.icon className="h-5 w-5" />
              </div>
              <h3 className="font-display text-base font-semibold text-ink">{cap.title}</h3>
              <p className="mt-1.5 text-sm text-ink-faint">{cap.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Business benefits */}
      <section className="border-t border-surface-border bg-surface-sunken py-16">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-2xl font-semibold text-ink">Built for Real Businesses</h2>
          <p className="mt-2 max-w-2xl text-sm text-ink-faint">
            Domain-aware aspect extraction adapts to your industry automatically.
          </p>
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {benefits.map((b) => (
              <div key={b.title} className="rounded-lg border border-surface-border bg-white p-5">
                <b.icon className="h-5 w-5 text-brand" />
                <h3 className="mt-3 font-medium text-ink">{b.title}</h3>
                <p className="mt-1.5 text-xs leading-relaxed text-ink-faint">{b.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-6 py-16 text-center">
        <h2 className="font-display text-2xl font-semibold text-ink sm:text-3xl">
          Turn Customer Feedback into Business Decisions.
        </h2>
        <div className="mt-6">
          <Link
            to="/analyze"
            className="inline-flex items-center gap-2 rounded-md bg-brand px-6 py-3 text-sm font-semibold text-white shadow-pop transition hover:bg-brand-dark focus-ring"
          >
            Get Started <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </div>
  )
}
