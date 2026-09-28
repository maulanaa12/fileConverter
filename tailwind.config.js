/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./templates/**/*.html', './static/js/**/*.js'],
  theme: {
    extend: {
      colors: {
        // Temporary red palette based on the iLovePDF visual reference.
        // The action shade is darker than the reference red for readable white labels.
        brand: {
          50: '#fff5f4',
          100: '#ffe7e5',
          200: '#ffc6c2',
          300: '#ffaaa4',
          400: '#f06560',
          500: '#d52b27',
          600: '#c42924',
          700: '#ab211d',
          800: '#831d19',
          900: '#591714',
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
