/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#6366f1',
        secondary: '#ec4899',
        dark: '#0f172a',
        light: '#f8fafc',
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
