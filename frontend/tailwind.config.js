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
        // ── Student — Forest Green ──
        student: {
          DEFAULT: '#2F5D50',   // Primary — Forest Green
          hover: '#254A40',     // Primary Hover — Deep Forest
          mist: '#EEF4F1',     // Soft Background — Sage Mist
          moss: '#E3ECE7',     // Section Background — Soft Moss
          ink: '#1E2E29',       // Headings — Deep Pine
          text: '#5E6B65',      // Body Text — Olive Slate
        },
        // ── School — Sapphire Blue ──
        school: {
          DEFAULT: '#1F4E79',   // Primary — Sapphire Blue
          hover: '#183C5D',     // Primary Hover — Deep Sapphire
          mist: '#EFF5FA',     // Soft Background — Ice Blue
          moss: '#E4EDF5',     // Section Background — Mist Blue
          ink: '#162535',       // Headings — Midnight Blue
          text: '#5D6B78',      // Body Text — Steel Slate
        },
        // ── Shared gold accent ──
        gold: {
          DEFAULT: '#C89A3D',   // Brand Accent — Warm Gold
          hover: '#AE8433',     // Hover Accent — Burnished Gold
          soft: '#F8F1E2',      // Soft Accent Bg — Cream Gold
          pale: '#F3E6C7',     // Accent Soft — Pale Gold
        },
        // ── Shared neutrals ──
        offwhite: '#FAFBF9',    // Main Background — Off White
        charcoal: '#202529',    // Dark Text — Charcoal Ink
        slate: '#667085',       // Secondary Text — Muted Slate
        stone: '#D9E1DC',       // Border — Soft Stone
        divider: '#E9EEEB',     // Light Divider — Mist Gray
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
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        heading: ['Lora', 'serif'],
        body: ['Inter', 'sans-serif'],
      },
      backgroundColor: {
        'student': '#FAFAF8',
        'institution': '#F8FAFC',
      },
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
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "float": "float 6s ease-in-out infinite",
        "float-slow": "float-slow 8s ease-in-out infinite",
        "orbit": "orbit 20s linear infinite",
        "pulse-soft": "pulse-soft 3s ease-in-out infinite",
        "bounce-gentle": "bounce-gentle 2s ease-in-out infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
