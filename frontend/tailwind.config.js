/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        glass: {
          light: 'rgba(255, 255, 255, 0.1)',
          dark: 'rgba(0, 0, 0, 0.3)',
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'flash-amber': 'flash-amber 1s ease-in-out infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 20px rgba(34, 197, 94, 0.5)' },
          '50%': { opacity: '0.8', boxShadow: '0 0 30px rgba(34, 197, 94, 0.8)' },
        },
        'flash-amber': {
          '0%, 100%': { backgroundColor: 'rgba(245, 158, 11, 0.2)' },
          '50%': { backgroundColor: 'rgba(245, 158, 11, 0.6)' },
        },
      },
    },
  },
  plugins: [],
}
