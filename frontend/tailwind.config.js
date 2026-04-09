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
        brand: {
          slate: {
            50: '#F0F3F9',
            100: '#E8EDF5',
            200: '#C9D3E8',
            300: '#A3B3D4',
            400: '#7A91BC',
            500: '#4E6A9E',
            600: '#3B5998',
            700: '#2C4370',
            800: '#1E2E4D',
            900: '#111B2E',
          },
          amber: {
            50: '#FFF8E7',
            100: '#FFEFC2',
            200: '#FFE08A',
            300: '#FFCF4D',
            400: '#F5B800',
            500: '#E5A100',
            600: '#B8820D',
            700: '#8C6310',
            800: '#6B4B0F',
            900: '#4A340D',
          },
        },
        // shadcn semantic colors (CSS variable based)
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Landing page color scales
        forest: {
          50: "#F2F5F0",
          100: "#E0E7DB",
          200: "#C1CFBA",
          300: "#A4AC86",
          400: "#6B7A5A",
          500: "#4A6345",
          600: "#2D4A2B",
          700: "#223A21",
          800: "#1A2E1A",
          900: "#0F1C0F",
        },
        sage: {
          300: "#A8AE9C",
          400: "#8F9682",
          500: "#7D8471",
          600: "#686F5E",
        },
        gold: {
          50: "#FFF8E7",
          100: "#FFEFC2",
          200: "#FFE08A",
          300: "#FFCF4D",
          400: "#F5B800",
          500: "#E5A100",
          600: "#B8820D",
          700: "#8C6310",
        },
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
