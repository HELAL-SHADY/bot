import type { Config } from 'tailwindcss';

export default {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#0B0B0B',
        surface: '#1A1A1A',
        accent: '#4F46E5',
        text: '#FFFFFF'
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(79,70,229,0.25), 0 10px 40px rgba(79,70,229,0.2)'
      }
    }
  },
  plugins: []
} satisfies Config;
