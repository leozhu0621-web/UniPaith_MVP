// Skip-to-content link (Spec 80 §3 / WCAG 2.4.1) — the first focusable element
// in every layout; visually hidden until keyboard-focused, then jumps past the
// nav chrome to <main id="main">.
export default function SkipLink() {
  return (
    <a
      href="#main"
      className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[100] focus:rounded-lg focus:bg-card focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-foreground focus:elev-raised focus:outline-none focus:ring-2 focus:ring-ring"
    >
      Skip to content
    </a>
  )
}
