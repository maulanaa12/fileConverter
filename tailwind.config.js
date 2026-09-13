/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./templates/**/*.html', './static/js/**/*.js'],
  theme: {
    extend: {
      colors: {
        // Teal ramp shifted one stop so brand-500 = #0D9488 (primary).
        // Keeps existing bg-brand-500 / hover:bg-brand-600 classes pixel-correct.
        brand: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#14b8a6',
          500: '#0d9488',
          600: '#0f766e',
          700: '#115e59',
          800: '#134e4a',
          900: '#042f2e',
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        'modal-pop': {
          from: { opacity: '0', transform: 'scale(.96)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        'fade-fast': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
      },
      animation: {
        'modal-pop': 'modal-pop .2s cubic-bezier(.16,1,.3,1)',
        'fade-fast': 'fade-fast .15s ease-out',
      },
    },
  },
  plugins: [],
};
