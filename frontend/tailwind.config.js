/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans:  ['Inter', 'system-ui', 'sans-serif'],
        brand: ['"Cormorant Garamond"', 'Georgia', 'serif'],
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
        card:    '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        cardHov: '0 4px 16px rgba(37, 99, 235, 0.10)',
        soft:    '0 1px 4px rgba(0,0,0,0.05)',
      },
      animation: {
        'fade-in':  'fadeIn 0.35s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'scale-in': 'scaleIn 0.25s ease-out',
      },
      keyframes: {
        fadeIn:  { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(12px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        scaleIn: { '0%': { opacity: '0', transform: 'scale(0.97)' }, '100%': { opacity: '1', transform: 'scale(1)' } },
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      }
    },
  },
  plugins: [],
}
