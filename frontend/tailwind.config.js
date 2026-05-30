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
        // ── Authoritative brand palette (Brand Materials/colors_and_type.css) ──
        // Light theme: Sunlit Gold + Cobalt on warm Paper.
        // Existing student-*/school-*/gold-*/offwhite/charcoal tokens are
        // remapped to brand values so legacy class names still resolve.
        paper: '#FCFAF2',       // canonical warm-paper background
        ink: {
          DEFAULT: '#2A2724',   // soft-ink (body text on light)
          deep: '#0A1428',      // deep-ink (dark canvas)
          soft: '#2A2724',      // alias
        },
        cobalt: {
          DEFAULT: '#2A6BD4',   // links, eyebrows, secondary accents
          dark: '#6FA0E8',      // lifted cobalt on dark
          hover: '#1F58B5',     // pressed cobalt
        },
        cream: {
          DEFAULT: '#F5F1E8',   // dark-theme text + lowercase on dark wordmark
          warm: '#F5F1E8',
        },
        // ── Student namespace (now Sunlit Gold = brand primary) ──
        student: {
          DEFAULT: '#FFD60A',   // sunlit-gold — primary CTA
          hover: '#E5C000',     // pressed gold
          mist: '#F2EEE0',      // warm-muted layer
          moss: '#F5F1E8',      // soft cream section bg
          ink: '#0A1428',       // editorial deep-ink for headings
          text: '#4A4640',      // muted warm-gray body
        },
        // ── School namespace (Cobalt = brand secondary) ──
        school: {
          DEFAULT: '#2A6BD4',
          hover: '#1F58B5',
          mist: '#F2EEE0',
          moss: '#F5F1E8',
          ink: '#0A1428',
          text: '#4A4640',
        },
        // ── Gold accent (matches primary Sunlit Gold) ──
        gold: {
          DEFAULT: '#FFD60A',
          hover: '#E5C000',
          soft: '#FFF1B0',
          pale: '#FFE680',
          dark: '#F2C800',      // dark-theme gold
        },
        // ── Shared neutrals (warm-paper system) ──
        offwhite: '#FCFAF2',
        charcoal: '#2A2724',
        slate: '#4A4640',
        stone: '#C9C2A8',
        divider: '#F2EEE0',
        // ── Semantic status (canonical from colors_and_type.css §State) ──
        success: {
          DEFAULT: '#2E7D5B',
          soft:    '#DCE8DA',
          dark:    '#6FCB95',
          'dark-soft': '#1E3A2A',
        },
        warning: {
          DEFAULT: '#C58A12',
          soft:    '#F5E6CC',
          dark:    '#F0B964',
          'dark-soft': '#3D2E18',
        },
        error: {
          DEFAULT: '#B8412B',
          soft:    '#F2D7D0',
          dark:    '#FF8470',
          'dark-soft': '#3D1E1A',
        },
        info: {
          DEFAULT: '#2A6BD4',   // same as cobalt
          dark:    '#6FA0E8',
        },
        // ── Legacy brand scales (product dashboards — migrate separately) ──
        brand: {
          slate: {
            50: '#F0F3F9', 100: '#E8EDF5', 200: '#C9D3E8', 300: '#A3B3D4',
            400: '#7A91BC', 500: '#4E6A9E', 600: '#3B5998', 700: '#2C4370',
            800: '#1E2E4D', 900: '#111B2E',
          },
          amber: {
            50: '#FFF8E7', 100: '#FFEFC2', 200: '#FFE08A', 300: '#FFCF4D',
            400: '#F5B800', 500: '#E5A100', 600: '#B8820D', 700: '#8C6310',
          },
        },
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
        // Europa loads via Adobe Typekit kit spe3ioy; family name lowercase 'europa'.
        // Kit ships 300/400/700 (+italics) only — no 600 cut, see fontWeight below.
        sans: ['europa', 'system-ui', '-apple-system', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
        body: ['europa', 'system-ui', '-apple-system', '"Segoe UI"', 'Roboto', 'sans-serif'],
        // Backwards-compat aliases so legacy classes still resolve to Europa
        // until grep+replace lands. Heading is Europa, NOT EB Garamond.
        heading: ['europa', 'system-ui', '-apple-system', '"Segoe UI"', 'Roboto', 'sans-serif'],
        hwDisplay: ['europa', 'system-ui', 'sans-serif'],
        hwNote: ['europa', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'SF Mono', 'Menlo', 'Consolas', 'monospace'],
      },
      fontWeight: {
        light: '300',
        normal: '400',
        // Kit has no 600 cut — semibold aliased to bold to prevent
        // browser-synthesized fake weights.
        semibold: '700',
        bold: '700',
      },
      fontSize: {
        // Brand type scale per Spec/01 §3.3.
        display:  ['4.5rem',   { lineHeight: '1.05', letterSpacing: '-0.02em',  fontWeight: '700' }],
        h1:       ['3rem',     { lineHeight: '1.08', letterSpacing: '-0.015em', fontWeight: '700' }],
        h2:       ['1.75rem',  { lineHeight: '1.20', letterSpacing: '0',        fontWeight: '700' }],
        h3:       ['1.25rem',  { lineHeight: '1.30', letterSpacing: '0',        fontWeight: '700' }],
        body:     ['1rem',     { lineHeight: '1.60' }],
        small:    ['0.875rem', { lineHeight: '1.50' }],
        eyebrow:  ['0.75rem',  { lineHeight: '1.20', letterSpacing: '0.22em',   fontWeight: '700' }],
        label:    ['0.8125rem',{ lineHeight: '1.20',                            fontWeight: '700' }],
      },
      borderRadius: {
        xs:    '4px',
        sm:    '6px',
        md:    '10px',
        DEFAULT:'14px',
        lg:    'var(--radius)',
        xl:    '22px',
        pill:  '9999px',
      },
      boxShadow: {
        subtle: '0 1px 2px rgba(10,20,40,.06), 0 1px 1px rgba(10,20,40,.04)',
        raised: '0 6px 16px -4px rgba(10,20,40,.12), 0 2px 4px rgba(10,20,40,.06)',
        glow:   '0 0 0 4px rgba(255,214,10,.18), 0 10px 30px -8px rgba(255,214,10,.45)',
      },
      transitionTimingFunction: {
        'brand-out':    'cubic-bezier(0.2, 0.7, 0.2, 1)',
        'brand-in-out': 'cubic-bezier(0.65, 0.05, 0.36, 1)',
      },
      transitionDuration: {
        fast: '120ms',
        base: '200ms',
        slow: '360ms',
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
          "0%": { opacity: "0", transform: "translateY(6px)" },
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
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "float": "float 6s ease-in-out infinite",
        "float-slow": "float-slow 8s ease-in-out infinite",
        "orbit": "orbit 20s linear infinite",
        "pulse-soft": "pulse-soft 3s ease-in-out infinite",
        "bounce-gentle": "bounce-gentle 2s ease-in-out infinite",
        "page-in": "page-in 0.2s ease-out",
        "fade-in": "fade-in 0.15s ease-out",
        "slide-in-right": "slide-in-right 0.2s ease-out",
        "slide-in-left": "slide-in-left 0.2s ease-out",
        "scale-in": "scale-in 0.15s ease-out",
        "slide-up-fade": "slide-up-fade 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
