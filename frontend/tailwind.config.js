/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4f46e5',
        secondary: '#7c3aed',
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
