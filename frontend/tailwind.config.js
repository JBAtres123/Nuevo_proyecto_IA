/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',

  content: [
    './index.html',
    './src/**/*.{vue,js,ts}',
  ],

  theme: {
    extend: {
      fontFamily: {
        display: ['Gorditas', 'serif'],
        body: ['DM Sans', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },

      colors: {
        brand: {
          50:  '#f7ffe8',
          100: '#edffc2',
          200: '#ddff8a',
          300: '#c8f060',
          400: '#b4e63e',
          500: '#9ccd25',
          600: '#7da31c',
          700: '#5e7a18',
          800: '#435614',
          900: '#2a3610',
        },

        accent: {
          green: '#c8f060',
          blue: '#60a8f0',
          pink: '#f06090',
          orange: '#f0a03c',
        },

        surface: {
        /*
          MODO CLARO
          Verde pastel cálido, suave y amigable.
          Mantiene identidad visual sin verse chillante.
        */
        DEFAULT: '#f5f8ee',
        card: '#ffffff',
        cardSoft: '#fbfdf6',
        nav: '#f0f7df',
        border: '#dbe5cf',
        borderStrong: '#c7d6b6',

        text: '#070707',
        muted: '#050505',
        mutedSoft: '#080808',

        tag: '#edf6dc',
        table: '#ffffff',
        tableHover: '#f2f8e8',

        /*
          MODO OSCURO
        */
          dark: '#0e0f11',
          cardDark: '#161719',
          cardSoftDark: '#1b1c1f',
          borderDark: '#2a2b2f',
          borderStrongDark: '#3a3c41',

          textDark: '#e8e9ec',
          mutedDark: '#9ca3af',
          mutedSoftDark: '#6b6d75',

          tagDark: '#1e2024',
          tableDark: '#161719',
          tableHoverDark: '#1e2024',
        },
      },

      boxShadow: {
        soft: '0 4px 20px rgba(0,0,0,0.06)',
        card: '0 6px 24px rgba(0,0,0,0.10)',
        neon: '0 0 18px rgba(200,240,96,0.35)',
      },

      borderRadius: {
        '2xl': '1.25rem',
      },

      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'pulse-slow': 'pulse 3s infinite',
      },

      keyframes: {
        fadeIn: {
          from: { opacity: 0 },
          to: { opacity: 1 },
        },

        slideUp: {
          from: {
            opacity: 0,
            transform: 'translateY(16px)',
          },

          to: {
            opacity: 1,
            transform: 'translateY(0)',
          },
        },
      },
    },
  },

  plugins: [],
}