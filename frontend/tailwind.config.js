/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        graphite: '#14161A',
        surface: '#1C1F26',
        bullion: '#C9A15A',
        primary: '#EDEEF0',
        muted: '#8B909C',
        'text-primary': '#EDEEF0',
        'text-muted': '#8B909C',
        'line-hairline': '#2A2E37',
        'status-approved': '#4E9E6E',
        'status-vetoed': '#B5514A',
        'status-warning': '#C9A15A',
        'session-asian': '#5B7FA6',
        'session-london': '#4E9E8F',
        'session-ny': '#B8763F',
      },
    },
  },
  plugins: [],
}
