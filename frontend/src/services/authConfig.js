// Whether Clerk authentication is configured for this deployment.
//
// CXIQ works fully without this — every feature (single analysis, batch
// upload, dashboard, compare languages, ask CXIQ) works for guests. Setting
// VITE_CLERK_PUBLISHABLE_KEY simply adds a "Sign In" button and ties
// uploaded datasets to a personal account (see "My Datasets" on the
// Dashboard) — nothing else in the app changes or requires it.
export const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || ''
export const isAuthConfigured = Boolean(CLERK_PUBLISHABLE_KEY)
