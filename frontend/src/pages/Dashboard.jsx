import { useEffect, useState, useCallback } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { SignedIn, SignedOut } from '@clerk/clerk-react'
import {
  Download,
  TrendingUp,
  AlertTriangle,
  Lightbulb,
  ListChecks,
  RefreshCw,
  Globe2,
} from 'lucide-react'

import {
  getDashboard,
  downloadResults,
  getMyDatasets,
  retryFailedTranslations,
} from '../services/api.js'

import { isAuthConfigured } from '../services/authConfig.js'
import {
  Section,
  LoadingState,
  ErrorState,
  EmptyState,
} from '../components/States.jsx'

import GetStartedActions from '../components/GetStartedActions.jsx'
import StatCard from '../components/StatCard.jsx'
import CustomerVoiceTable from '../components/CustomerVoiceTable.jsx'
import IssueRadar from '../components/IssueRadar.jsx'
import DecisionCenter from '../components/DecisionCenter.jsx'
import LanguageComparisonTable from '../components/LanguageComparisonTable.jsx'
import AskCxiq from '../components/AskCxiq.jsx'

import {
  SentimentDonut,
  EmotionBarChart,
  PriorityBarChart,
  SentimentTrendChart,
  CategorySentimentChart,
} from '../components/Charts.jsx'


// =========================================================
// CX SCORE LABEL COLORS
// =========================================================

const CX_LABEL_COLOR = {
  Excellent: 'positive',
  Good: 'brand',
  'Needs Attention': 'gold',
  Critical: 'negative',
}


// =========================================================
// AUTO RESOLVE DASHBOARD
// =========================================================

function DashboardAutoResolve() {
  const navigate = useNavigate()

  const [state, setState] = useState('checking')

  useEffect(() => {
    let alive = true

    getMyDatasets()
      .then((list) => {
        if (!alive) return

        if (list && list.length > 0) {
          navigate(
            `/dashboard?dataset_id=${list[0].dataset_id}`,
            { replace: true }
          )
        } else {
          setState('none')
        }
      })
      .catch(() => {
        if (alive) {
          setState('none')
        }
      })

    return () => {
      alive = false
    }
  }, [navigate])


  if (state === 'checking') {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16">
        <LoadingState message="Loading your dashboard..." />
      </div>
    )
  }


  return (
    <div className="mx-auto max-w-6xl px-6 py-16">
      <EmptyState
        title="Welcome to CXIQ"
        description="You haven't analyzed any datasets yet."
        action={
          <GetStartedActions className="mt-2" />
        }
      />
    </div>
  )
}


// =========================================================
// MAIN DASHBOARD
// =========================================================

export default function Dashboard() {
  const [searchParams] = useSearchParams()

  const datasetIdParam =
    searchParams.get('dataset_id')


  // If a dataset ID was explicitly provided,
  // always load that dataset.
  if (datasetIdParam) {
    return (
      <DashboardView
        datasetId={datasetIdParam}
      />
    )
  }


  // If authentication is not configured,
  // use the bundled sample dataset.
  if (!isAuthConfigured) {
    return (
      <DashboardView
        datasetId="sample"
      />
    )
  }


  return (
    <>
      <SignedIn>
        <DashboardAutoResolve />
      </SignedIn>

      <SignedOut>
        <DashboardView datasetId="sample" />
      </SignedOut>
    </>
  )
}


// =========================================================
// DASHBOARD VIEW
// =========================================================

function DashboardView({ datasetId }) {
  const [searchParams, setSearchParams] =
    useSearchParams()

  const languageParam =
    searchParams.get('language') || 'All'


  // -------------------------------------------------------
  // STATE
  // -------------------------------------------------------

  const [status, setStatus] =
    useState('loading')

  const [error, setError] =
    useState('')

  const [data, setData] =
    useState(null)

  const [downloading, setDownloading] =
    useState(false)

  const [downloadError, setDownloadError] =
    useState('')

  const [retrying, setRetrying] =
    useState(false)

  const [retryMessage, setRetryMessage] =
    useState('')


  // -------------------------------------------------------
  // LOAD DASHBOARD
  // -------------------------------------------------------

  const load = useCallback(() => {
    setStatus('loading')
    setError('')

    getDashboard(
      datasetId,
      languageParam
    )
      .then((res) => {
        setData(res)
        setStatus('done')
      })
      .catch((err) => {
        setError(err.message)
        setStatus('error')
      })
  }, [datasetId, languageParam])


  useEffect(() => {
    load()
  }, [load])


  // -------------------------------------------------------
  // LANGUAGE FILTER
  // -------------------------------------------------------

  function handleLanguageChange(lang) {
    const params =
      new URLSearchParams(searchParams)

    if (lang === 'All') {
      params.delete('language')
    } else {
      params.set('language', lang)
    }

    setSearchParams(params)
  }


  // -------------------------------------------------------
  // AUTHENTICATED CSV DOWNLOAD
  // -------------------------------------------------------

  async function handleDownload() {
    if (downloading) return

    try {
      setDownloading(true)
      setDownloadError('')

      await downloadResults(datasetId)

    } catch (err) {
      console.error(
        'CXIQ download failed:',
        err
      )

      setDownloadError(
        err.message ||
        'Could not download the results CSV.'
      )

    } finally {
      setDownloading(false)
    }
  }


  // -------------------------------------------------------
  // RETRY FAILED TRANSLATIONS
  //
  // Unlike `load()` (which just re-reads whatever is already stored),
  // this actually re-attempts translation + analysis for reviews that
  // failed the first time, then reloads the dashboard so the updated
  // results show up.
  // -------------------------------------------------------

  async function handleRetryFailed() {
    if (retrying) return

    try {
      setRetrying(true)
      setRetryMessage('')

      const summary = await retryFailedTranslations(datasetId)

      if (summary.attempted === 0) {
        setRetryMessage('No failed reviews to retry.')
      } else {
        setRetryMessage(
          `Retried ${summary.attempted} review${summary.attempted === 1 ? '' : 's'} — ` +
          `${summary.now_reliable} now translated successfully` +
          (summary.still_unreliable > 0
            ? `, ${summary.still_unreliable} still couldn't be translated.`
            : '.')
        )
      }

      load()

    } catch (err) {
      console.error(
        'CXIQ retry-failed-translations failed:',
        err
      )

      setRetryMessage(
        err.message ||
        'Could not retry failed translations.'
      )

    } finally {
      setRetrying(false)
    }
  }


  // -------------------------------------------------------
  // LOADING STATE
  // -------------------------------------------------------

  if (status === 'loading') {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16">
        <LoadingState message="Building your dashboard..." />
      </div>
    )
  }


  // -------------------------------------------------------
  // ERROR STATE
  // -------------------------------------------------------

  if (status === 'error') {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16">

        <ErrorState
          message={error}
          onRetry={load}
        />

        <div className="mt-4 text-center">
          <Link
            to="/analyze"
            className="text-sm font-medium text-brand hover:underline"
          >
            Go analyze some feedback first →
          </Link>
        </div>

      </div>
    )
  }


  // -------------------------------------------------------
  // EMPTY DATA
  // -------------------------------------------------------

  if (
    !data ||
    !data.kpis ||
    data.kpis.reviews_analyzed === 0
  ) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16">

        <EmptyState
          title="No analyzed data yet"
          description={
            data?.message ||
            'Upload a dataset on the Analyze page to populate this dashboard.'
          }
          action={
            <Link
              to="/analyze"
              className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark"
            >
              Go to Analyze
            </Link>
          }
        />

      </div>
    )
  }


  // -------------------------------------------------------
  // DASHBOARD DATA
  // -------------------------------------------------------

  const {
    kpis,
    sentiment_distribution,
    emotion_distribution,
    priority_distribution,
    trends,
    business_insights,
    recommendations,
    sentiment_by_category,
    customer_voice,
    issue_radar,
    decision_center,
    language_breakdown,
    available_languages,
    translation_health,
  } = data


  // =======================================================
  // DASHBOARD UI
  // =======================================================

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">


      {/* =================================================
          TRANSLATION WARNING
      ================================================= */}

      {translation_health?.unreliable_reviews > 0 && (

        <div className="mb-6 flex items-start gap-3 rounded-lg border border-gold/30 bg-gold-light p-4 text-sm text-ink-soft">

          <Globe2 className="mt-0.5 h-4 w-4 shrink-0 text-gold" />

          <div>

            <p className="font-medium text-ink">

              {translation_health.unreliable_reviews}{' '}

              review{
                translation_health.unreliable_reviews === 1
                  ? ''
                  : 's'
              } could not be translated

            </p>

            <p className="mt-0.5 text-ink-faint">

              The translation service didn't respond for these
              non-English reviews, so they're shown as
              low-confidence/neutral instead of a guessed
              sentiment, and excluded from the sentiment,
              aspect, and CX Score statistics above. Use
              "Retry Failed Translations" below to try them
              again — the Refresh button only reloads this
              page and does not retry translation

              {translation_health.success_rate_pct != null &&
                ` — currently succeeding for ${translation_health.success_rate_pct}% of non-English reviews`
              }.

            </p>

            <button
              type="button"
              onClick={handleRetryFailed}
              disabled={retrying}
              className="mt-2 inline-flex items-center gap-2 rounded-md border border-gold/40 bg-white px-3 py-1.5 text-xs font-semibold text-ink hover:bg-gold-light focus-ring disabled:cursor-not-allowed disabled:opacity-60"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${retrying ? 'animate-spin' : ''}`} />
              {retrying ? 'Retrying...' : 'Retry Failed Translations'}
            </button>

            {retryMessage && (
              <p className="mt-1.5 text-xs text-ink-faint">
                {retryMessage}
              </p>
            )}

          </div>

        </div>

      )}


      {/* =================================================
          HEADER
      ================================================= */}

      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">

        <div>

          <h1 className="font-display text-2xl font-semibold text-ink sm:text-3xl">
            Dashboard
          </h1>

          <p className="mt-2 text-sm text-ink-faint">
            Customer experience intelligence across{' '}
            {kpis.reviews_analyzed.toLocaleString()}{' '}
            analyzed reviews.
          </p>

        </div>


        <div className="flex flex-wrap items-center gap-2">


          {/* LANGUAGE FILTER */}

          {available_languages?.length > 1 && (

            <select
              value={languageParam}
              onChange={(e) =>
                handleLanguageChange(
                  e.target.value
                )
              }
              className="rounded-md border border-surface-border bg-white px-3 py-2 text-sm text-ink focus-ring focus:border-brand"
            >

              <option value="All">
                All Languages
              </option>

              {available_languages.map(
                (lang) => (

                  <option
                    key={lang}
                    value={lang}
                  >
                    {lang}
                  </option>

                )
              )}

            </select>

          )}


          {/* REFRESH */}

          <button
            type="button"
            onClick={load}
            title="Reloads this dashboard from the currently stored results — it does not retry translation"
            className="inline-flex items-center gap-2 rounded-md border border-surface-border bg-white px-3 py-2 text-sm font-medium text-ink hover:bg-surface-sunken focus-ring"
          >

            <RefreshCw className="h-4 w-4" />

            Refresh

          </button>


          {/* DOWNLOAD RESULTS */}

          <button
            type="button"
            onClick={handleDownload}
            disabled={downloading}
            className="inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark focus-ring disabled:cursor-not-allowed disabled:opacity-60"
          >

            {downloading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Downloading...
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                Download Results CSV
              </>
            )}

          </button>

        </div>

      </div>


      {/* DOWNLOAD ERROR */}

      {downloadError && (

        <div className="mb-6 rounded-md border border-negative/20 bg-negative-light p-3 text-sm text-negative">

          {downloadError}

        </div>

      )}


      {/* =================================================
          ZONE 1 — CX PULSE
      ================================================= */}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">

        <StatCard
          label="Reviews Analyzed"
          value={
            kpis.reviews_analyzed.toLocaleString()
          }
        />

        <StatCard
          label="Positive"
          value={`${kpis.positive_pct}%`}
          accent="positive"
        />

        <StatCard
          label="Neutral"
          value={`${kpis.neutral_pct}%`}
        />

        <StatCard
          label="Negative"
          value={`${kpis.negative_pct}%`}
          accent="negative"
        />

        <StatCard
          label="CX Score"
          value={`${kpis.cx_score}/100`}
          sub={kpis.cx_label}
          accent={
            CX_LABEL_COLOR[
              kpis.cx_label
            ] || 'ink'
          }
        />

        <StatCard
          label="High / Critical Issues"
          value={
            kpis.high_critical_issues
          }
          accent="negative"
        />

      </div>


      {/* =================================================
          ZONE 2 — CUSTOMER VOICE
      ================================================= */}

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">

        <Section
          title="Sentiment Distribution"
          className="lg:col-span-1"
        >

          <SentimentDonut
            data={
              sentiment_distribution
            }
          />

          <div className="mt-2 flex justify-center gap-4 text-xs">

            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-positive" />
              Positive
            </span>

            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-neutralx" />
              Neutral
            </span>

            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-negative" />
              Negative
            </span>

          </div>

        </Section>


        <Section
          title="Customer Voice Intelligence"
          description="What customers talk about most, and how they feel about it"
          className="lg:col-span-2"
        >

          {customer_voice?.length > 0 ? (

            <CustomerVoiceTable
              data={customer_voice}
            />

          ) : (

            <EmptyState
              title="No aspects detected"
              description="This dataset may not contain domain-specific aspect language."
            />

          )}

        </Section>

      </div>


      {/* =================================================
          CATEGORY SENTIMENT
      ================================================= */}

      {sentiment_by_category?.length > 0 && (

        <div className="mt-6">

          <Section title="Sentiment by Category">

            <CategorySentimentChart
              data={
                sentiment_by_category
              }
            />

          </Section>

        </div>

      )}


      {/* =================================================
          ZONE 3 — ISSUE RADAR
      ================================================= */}

      <div className="mt-6">

        <Section
          title="🚨 CX Issue Radar"
          description="Emerging problems ranked by a calculated risk score (mention volume × negativity × severity × trend)"
        >

          <IssueRadar
            data={issue_radar}
          />

        </Section>

      </div>


      {/* =================================================
          EMOTION + PRIORITY
      ================================================= */}

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">

        <Section title="Emotion Analytics">

          <EmotionBarChart
            data={
              emotion_distribution
            }
          />

        </Section>


        <Section
          title="Issue / Complaint Intelligence"
          description="Reviews by complaint priority"
        >

          <PriorityBarChart
            data={
              priority_distribution
            }
          />

        </Section>

      </div>


      {/* =================================================
          ZONE 4 — MULTILINGUAL
      ================================================= */}

      {language_breakdown?.length > 1 && (

        <div className="mt-6">

          <Section
            title="🌐 Multilingual Intelligence"
            description="Language CX Comparison — sentiment and CX Score by detected language"
          >

            <LanguageComparisonTable
              data={
                language_breakdown
              }
            />

          </Section>

        </div>

      )}


      {/* =================================================
          ZONE 5 — TRENDS
      ================================================= */}

      <div className="mt-6">

        <Section
          title="Trends & Forecast"
          description="Sentiment over time, emerging issues, and a simple forward projection"
        >

          {trends.available ? (

            <div className="space-y-6">

              <SentimentTrendChart
                data={
                  trends.sentiment_over_time
                }
              />


              {trends.forecast?.available && (

                <div className="rounded-md border border-surface-border bg-surface-sunken p-4">

                  <div className="flex items-center gap-2 text-sm font-semibold text-ink">

                    <TrendingUp className="h-4 w-4 text-brand" />

                    CX Forecast

                  </div>


                  <p className="mt-1 text-sm text-ink-soft">

                    Based on the current trend line,
                    negative feedback is projected to{' '}

                    {trends.forecast.change_pct >= 0
                      ? 'rise'
                      : 'fall'
                    } by{' '}

                    <strong>
                      {Math.abs(
                        trends.forecast.change_pct
                      )} points
                    </strong>{' '}

                    over the next two periods
                    (a simple linear projection,
                    not a guarantee).

                  </p>

                </div>

              )}


              {issue_radar.length > 0 &&
              issue_radar.some(
                (i) =>
                  i.trend_increase_pp
              ) ? (

                <div>

                  <div className="mb-3 flex items-center gap-2 text-negative">

                    <AlertTriangle className="h-4 w-4" />

                    <p className="text-sm font-semibold">
                      Emerging Issue Trends
                    </p>

                  </div>


                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">

                    {issue_radar
                      .filter(
                        (i) =>
                          i.trend_increase_pp
                      )
                      .slice(0, 2)
                      .map(
                        (issue, i) => (

                          <div
                            key={i}
                            className="rounded-md border border-negative/20 bg-negative-light p-4"
                          >

                            <p className="text-sm font-semibold text-negative">

                              {issue.aspect}{' '}
                              complaints have increased by{' '}
                              {issue.trend_increase_pp}{' '}
                              points

                            </p>

                          </div>

                        )
                      )}

                  </div>

                </div>

              ) : (

                <p className="text-sm text-ink-faint">
                  {trends.emerging_issues_message ||
                    'No significantly emerging issues detected in this period.'}
                </p>

              )}

            </div>

          ) : (

            <EmptyState
              title="Trend analysis unavailable"
              description={
                trends.message
              }
            />

          )}

        </Section>

      </div>


      {/* =================================================
          ZONE 6 — DECISION CENTER
      ================================================= */}

      <div className="mt-6">

        <Section
          title="🎯 Decision Center"
          description="Evidence-based priorities with recommended owners"
        >

          <DecisionCenter
            data={
              decision_center
            }
          />

        </Section>

      </div>


      {/* =================================================
          INSIGHTS + RECOMMENDATIONS
      ================================================= */}

      <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">

        <Section title="AI Business Insights">

          <ul className="space-y-3">

            {business_insights.map(
              (insight, i) => (

                <li
                  key={i}
                  className="flex gap-2.5 text-sm text-ink-soft"
                >

                  <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-brand" />

                  <span>
                    {insight}
                  </span>

                </li>

              )
            )}

          </ul>

        </Section>


        <Section title="Recommended Actions">

          <ul className="space-y-3">

            {recommendations.map(
              (rec, i) => (

                <li
                  key={i}
                  className="flex gap-2.5 text-sm text-ink-soft"
                >

                  <ListChecks className="mt-0.5 h-4 w-4 shrink-0 text-gold" />

                  <span>
                    {rec}
                  </span>

                </li>

              )
            )}

          </ul>

        </Section>

      </div>


      {/* =================================================
          ZONE 7 — ASK CXIQ
      ================================================= */}

      <div className="mt-6">

        <Section
          title="💬 Ask CXIQ"
          description="Ask a question about your customer feedback in plain language"
        >

          <AskCxiq
            datasetId={
              datasetId
            }
          />

        </Section>

      </div>

    </div>
  )
}