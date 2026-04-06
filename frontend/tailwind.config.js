/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        lavender:    'var(--color-lavender)',
        lavendLight: 'var(--color-lavend-light)',
        lavendMid:   'var(--color-lavend-mid)',
        mint:        'var(--color-mint)',
        mintLight:   'var(--color-mint-light)',
        peach:       'var(--color-peach)',
        peachLight:  'var(--color-peach-light)',
        skyLight:    'var(--color-sky-light)',
        rose:        'var(--color-rose)',
        roseLight:   'var(--color-rose-light)',
        amber:       'var(--color-amber)',
        amberLight:  'var(--color-amber-light)',
        surface:     'var(--color-surface)',
        surfaceAlt:  'var(--color-surface-alt)',
        surfaceBorder: 'var(--color-border)',
        muted:       'var(--color-muted)',
        text:        'var(--color-text)',
        textSoft:    'var(--color-text-soft)',
      },
      boxShadow: {
        card:    '0 2px 20px rgba(124, 111, 247, 0.08)',
        cardHov: '0 8px 32px rgba(124, 111, 247, 0.18)',
        soft:    '0 1px 8px rgba(0,0,0,0.06)',
      },
      animation: {
        'fade-in':  'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.45s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
      },
      keyframes: {
        fadeIn:  { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(16px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        scaleIn: { '0%': { opacity: '0', transform: 'scale(0.96)' }, '100%': { opacity: '1', transform: 'scale(1)' } },
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      }
    },
  },
  plugins: [],
}
