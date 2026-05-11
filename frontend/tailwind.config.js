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
        // remapped to brand values so the ~100 component files using them
        // pick up the brand without a global search-and-replace.
        paper: '#FCFAF2',       // canonical warm-paper background
        ink: '#0A1428',         // canonical deep-ink for dark surfaces
        cobalt: {
          DEFAULT: '#2A6BD4',   // links, eyebrows, secondary accents
          dark: '#6FA0E8',      // lifted cobalt for ink backgrounds
        },
        cream: '#F5F1E8',       // dark-theme text, lowercase on dark wordmark
        // ── Student namespace (now Sunlit Gold = brand primary) ──
        student: {
          DEFAULT: '#FFD60A',   // sunlit gold — primary CTA
          hover: '#E5C000',     // darker gold for hover
          mist: '#F2EEE0',      // warm muted layer (replaces light-blue-gray)
          moss: '#F5F1E8',      // soft cream section background
          ink: '#0A1428',       // editorial deep-ink for headings
          text: '#4A4640',      // soft warm-gray body
        },
        // ── School namespace (Cobalt = brand secondary) ──
        school: {
          DEFAULT: '#2A6BD4',   // cobalt — secondary
          hover: '#1F58B5',     // deeper cobalt
          mist: '#F2EEE0',
          moss: '#F5F1E8',
          ink: '#0A1428',
          text: '#4A4640',
        },
        // ── Gold accent (now matches primary Sunlit Gold) ──
        gold: {
          DEFAULT: '#FFD60A',   // sunlit gold
          hover: '#E5C000',     // pressed gold
          soft: '#FFF1B0',      // pale gold tint for backgrounds
          pale: '#FFE680',      // accent soft
        },
        // ── Shared neutrals (warm-paper system) ──
        offwhite: '#FCFAF2',    // canvas — warm paper (was cool gray)
        charcoal: '#2A2724',    // soft ink text (was charcoal ink)
        slate: '#4A4640',       // muted body text (warm gray)
        stone: '#C9C2A8',       // warm border (was cool stone)
        divider: '#F2EEE0',     // warm divider tint
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
        // Body / UI: System UI sans (native, neutral) per brand spec.
        sans: ['system-ui', '-apple-system', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
        // Display / headings: EB Garamond serif (editorial).
        heading: ['"EB Garamond"', 'Garamond', '"Times New Roman"', 'serif'],
        body: ['system-ui', '-apple-system', '"Segoe UI"', 'Roboto', 'sans-serif'],
        // Handwriting accents: Caveat (hero highlights) + Kalam (marginalia).
        hwDisplay: ['"Caveat"', 'cursive'],
        hwNote: ['"Kalam"', 'cursive'],
      },
      // Note: bg-student and bg-school come from colors.student and colors.school
      // Old backgroundColor overrides for '#FAFAF8' and '#F8FAFC' removed — use bg-offwhite instead
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
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
