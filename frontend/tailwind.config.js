/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        liberal: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        fascist: {
          50: '#fef2f2',
          100: '#fee2e2',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        parchment: '#f5e6c8',
        ink: '#1a1a1a',
        gold: '#d4a742',
        bronze: '#cd7f32',
      },
      fontFamily: {
        'display': ['Bebas Neue', 'Impact', 'sans-serif'],
        'body': ['Crimson Text', 'Georgia', 'serif'],
        'mono': ['IBM Plex Mono', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.6s ease-out forwards',
        'pulse-glow': 'pulseGlow 2s infinite',
        'typewriter': 'typewriter 2s steps(40) forwards',
        'flicker': 'flicker 3s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(212, 167, 66, 0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(212, 167, 66, 0.6)' },
        },
        typewriter: {
          '0%': { width: '0' },
          '100%': { width: '100%' },
        },
        flicker: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
          '75%': { opacity: '0.95' },
        },
      },
    },
  },
  plugins: [],
}
