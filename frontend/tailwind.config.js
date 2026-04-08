/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
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
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      backgroundColor: {
        'student': '#FAFAF8',
        'institution': '#F8FAFC',
      },
    },
  },
  plugins: [],
};
