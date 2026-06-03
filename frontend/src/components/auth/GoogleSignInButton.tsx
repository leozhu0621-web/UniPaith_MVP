// "Continue with Google" — Cognito hosted-UI federated sign-in.
//
// Clicking redirects to the Cognito hosted UI with `identity_provider=Google`,
// which bounces straight to Google's consent screen and back to
// `/auth/callback?code=...`. AuthCallbackPage then posts the code to
// `/auth/google-callback`, where the backend exchanges it for tokens and
// find-or-creates the student (see auth_service.google_callback).
//
// The two values below are PUBLIC (the Cognito hosted-UI domain and the SPA
// app-client id) — safe to ship in the bundle. They're overridable per
// environment via Vite env vars, with the production values as fallbacks.

const COGNITO_DOMAIN =
  (import.meta.env.VITE_COGNITO_DOMAIN as string | undefined) ||
  'unipaith.auth.us-east-1.amazoncognito.com'

const COGNITO_CLIENT_ID =
  (import.meta.env.VITE_COGNITO_CLIENT_ID as string | undefined) ||
  '3fo4t4114fr9opag803jdpbits'

// Only show the button in a built/deployed app. Local `vite dev` runs the
// Cognito-bypass email login, where a hosted-UI redirect (which would send the
// user to the production callback URL) can't complete.
const ENABLED = import.meta.env.PROD || Boolean(import.meta.env.VITE_COGNITO_DOMAIN)

function GoogleGlyph() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"
      />
      <path
        fill="#FBBC05"
        d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"
      />
    </svg>
  )
}

export default function GoogleSignInButton() {
  const signInWithGoogle = () => {
    const redirectUri = `${window.location.origin}/auth/callback`
    const params = new URLSearchParams({
      client_id: COGNITO_CLIENT_ID,
      response_type: 'code',
      scope: 'email openid profile',
      redirect_uri: redirectUri,
      identity_provider: 'Google',
      state: 'role:student',
    })
    window.location.href = `https://${COGNITO_DOMAIN}/oauth2/authorize?${params.toString()}`
  }

  if (!ENABLED) return null

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span className="h-px flex-1 bg-border" /> or <span className="h-px flex-1 bg-border" />
      </div>
      <button
        type="button"
        onClick={signInWithGoogle}
        className="flex w-full items-center justify-center gap-3 rounded-lg border border-border bg-card px-4 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        <GoogleGlyph />
        Continue with Google
      </button>
    </div>
  )
}
