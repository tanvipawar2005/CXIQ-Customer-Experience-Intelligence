/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#10151F',
          soft: '#3A4250',
          faint: '#6B7280',
        },
        surface: {
          DEFAULT: '#F5F7F7',
          card: '#FFFFFF',
          sunken: '#EEF1F1',
          border: '#E1E6E6',
        },
        brand: {
          DEFAULT: '#0F6B5C',
          dark: '#0B5347',
          light: '#E4F1EE',
          tint: '#12816F',
        },
        gold: {
          DEFAULT: '#C98A2B',
          light: '#FBF0DF',
        },
        positive: { DEFAULT: '#1F8A5F', light: '#E4F5EC' },
        neutralx: { DEFAULT: '#8A8F98', light: '#EEF0F1' },
        negative: { DEFAULT: '#C4432B', light: '#FBEAE6' },
        priority: {
          low: '#4C8C6B',
          medium: '#C9972B',
          high: '#C4622C',
          critical: '#9B2C2C',
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"Inter"', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(16, 21, 31, 0.04), 0 1px 0 rgba(16, 21, 31, 0.03)',
        pop: '0 8px 24px rgba(16, 21, 31, 0.08)',
      },
      borderRadius: {
        sm: '6px',
        md: '10px',
        lg: '16px',
      },
    },
  },
  plugins: [],
}
