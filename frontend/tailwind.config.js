/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // ── Legacy fixed-hex brand aliases REMOVED (Spec 65 — visual unification).
        // Every component now uses the semantic shadcn tokens below, which are
        // dark-mode safe. The old paper/ink/cobalt/cream/student-*/school-*/
        // gold-*/offwhite/charcoal/slate/stone/divider aliases were migrated
        // 1:1 via codemod (140 files) and deleted so they can't be reintroduced.
        // ── Status colors (Spec/01-brand-tokens.md §2.3 / §8) ──
        // DEFAULT + soft consume the CSS vars (defined in index.css :root AND .dark)
        // so bg-*-soft / text-* auto-flip in dark mode — fixes the status-tint
        // dark-mode leak app-wide. The static dark / dark-soft keys are kept for
        // backward-compat with any explicit `dark:*-dark` usages (now redundant).
        success: { DEFAULT: 'hsl(var(--success))', soft: 'hsl(var(--success-soft))', dark: '#6FCB95', 'dark-soft': '#1E3A2A' },
        warning: { DEFAULT: 'hsl(var(--warning))', soft: 'hsl(var(--warning-soft))', dark: '#F0B964', 'dark-soft': '#3D2E18' },
        error:   { DEFAULT: 'hsl(var(--error))', soft: 'hsl(var(--error-soft))', dark: '#FF8470', 'dark-soft': '#3D1E1A' },
        // ── shadcn semantic (CSS variable based) ──
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
        destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        accent: { DEFAULT: "hsl(var(--accent))", foreground: "hsl(var(--accent-foreground))" },
        popover: { DEFAULT: "hsl(var(--popover))", foreground: "hsl(var(--popover-foreground))" },
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
      },
      fontFamily: {
        // One font — Europa (Adobe Typekit kit spe3ioy, lowercase family name).
        // Hierarchy comes from size/weight/tracking, never a second typeface.
        // `heading` is aliased to the same stack so any legacy `font-heading`
        // class renders Europa rather than a serif. (Spec/01-brand-tokens.md §3.)
        sans: ['europa', 'system-ui', '-apple-system', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
        body: ['europa', 'system-ui', '-apple-system', '"Segoe UI"', 'Roboto', 'sans-serif'],
        heading: ['europa', 'system-ui', '-apple-system', '"Segoe UI"', 'Roboto', 'sans-serif'],
      },
      fontWeight: {
        // Europa kit spe3ioy: enable "Medium" (500) in the Adobe Fonts kit so
        // font-medium renders a REAL cut instead of a synthesized one. Semibold
        // still aliases to 700 (no 600 cut, by brand intent).
        light: '300',
        normal: '400',
        medium: '500',
        semibold: '700',
        bold: '700',
      },
      fontSize: {
        // Brand type scale (Spec/01-brand-tokens.md §3.3 / §8). Additive utilities.
        display:  ['4.5rem',   { lineHeight: '1.05', letterSpacing: '-0.02em',  fontWeight: '700' }],
        h1:       ['3rem',     { lineHeight: '1.08', letterSpacing: '-0.015em', fontWeight: '700' }],
        h2:       ['1.75rem',  { lineHeight: '1.20', letterSpacing: '0',        fontWeight: '700' }],
        h3:       ['1.25rem',  { lineHeight: '1.30', letterSpacing: '0',        fontWeight: '700' }],
        eyebrow:  ['0.75rem',  { lineHeight: '1.20', letterSpacing: '0.22em',   fontWeight: '700' }],
        label:    ['0.8125rem',{ lineHeight: '1.20',                            fontWeight: '700' }],
      },
      // Note: bg-student and bg-school come from colors.student and colors.school
      // Old backgroundColor overrides for '#FAFAF8' and '#F8FAFC' removed — use bg-offwhite instead
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        pill: "9999px",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-20px)" },
        },
        "float-slow": {
          "0%, 100%": { transform: "translateY(0px) rotate(0deg)" },
          "50%": { transform: "translateY(-30px) rotate(5deg)" },
        },
        "orbit": {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        "pulse-soft": {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "0.8" },
        },
        "bounce-gentle": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-6px)" },
        },
        "page-in": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-in-right": {
          "0%": { opacity: "0", transform: "translateX(12px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "slide-in-left": {
          "0%": { opacity: "0", transform: "translateX(-12px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.97)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "slide-up-fade": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        // ── Exit counterparts (UX overhaul §2) — driven by usePresence so
        // overlays animate OUT before unmounting. `forwards` fill in the
        // animation shorthand holds the final (hidden) frame until unmount.
        "fade-out": {
          "0%": { opacity: "1" },
          "100%": { opacity: "0" },
        },
        "scale-out": {
          "0%": { opacity: "1", transform: "scale(1)" },
          "100%": { opacity: "0", transform: "scale(0.97)" },
        },
        "slide-out-right": {
          "0%": { opacity: "1", transform: "translateX(0)" },
          "100%": { opacity: "0", transform: "translateX(12px)" },
        },
        "slide-down-fade": {
          "0%": { opacity: "1", transform: "translateY(0)" },
          "100%": { opacity: "0", transform: "translateY(4px)" },
        },
        // Bottom-docked tray (CompareTray) — a fuller rise/drop than the 4px fades.
        "tray-in": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "tray-out": {
          "0%": { opacity: "1", transform: "translateY(0)" },
          "100%": { opacity: "0", transform: "translateY(12px)" },
        },
        "page-loader-sweep": {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(400%)" },
        },
      },
      animation: {
        // Motion utilities consume the index.css tokens (UX overhaul §2) so
        // the easing/duration vocabulary lives in ONE place. Decorative loops
        // (float/orbit/pulse) keep their own long cycles.
        "accordion-down": "accordion-down var(--dur-base) var(--ease-out)",
        "accordion-up": "accordion-up var(--dur-base) var(--ease-in)",
        "float": "float 6s ease-in-out infinite",
        "float-slow": "float-slow 8s ease-in-out infinite",
        "orbit": "orbit 20s linear infinite",
        "pulse-soft": "pulse-soft 3s ease-in-out infinite",
        "bounce-gentle": "bounce-gentle 2s ease-in-out infinite",
        "page-in": "page-in var(--dur-page) var(--ease-entrance)",
        "fade-in": "fade-in var(--dur-fast) var(--ease-out)",
        "slide-in-right": "slide-in-right var(--dur-base) var(--ease-entrance)",
        "slide-in-left": "slide-in-left var(--dur-base) var(--ease-entrance)",
        "scale-in": "scale-in var(--dur-fast) var(--ease-out)",
        "slide-up-fade": "slide-up-fade var(--dur-base) var(--ease-entrance)",
        "fade-out": "fade-out var(--dur-fast) var(--ease-in) forwards",
        "scale-out": "scale-out var(--dur-fast) var(--ease-in) forwards",
        "slide-out-right": "slide-out-right var(--dur-base) var(--ease-in) forwards",
        "slide-down-fade": "slide-down-fade var(--dur-base) var(--ease-in) forwards",
        "tray-in": "tray-in var(--dur-base) var(--ease-out)",
        "tray-out": "tray-out var(--dur-base) var(--ease-in) forwards",
        // Tab panel swap — fade/rise keyed on the active tab (reuses the
        // slide-up-fade keyframes; apparent enough to read as a transition).
        "tab-panel-in": "slide-up-fade 260ms var(--ease-entrance)",
        "page-loader-sweep": "page-loader-sweep 1.4s var(--ease-out) infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
