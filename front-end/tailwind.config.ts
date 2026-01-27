import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ["class"],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Primary Colors (Brand Identity)
        primary: {
          50: '#EBF4FF',
          100: '#C3DAFE',
          200: '#A3BFFA',
          300: '#7F9CF5',
          400: '#667EEA',
          500: '#1A365D', // Primary brand - Deep Navy
          600: '#152A4A',
          700: '#102038',
          800: '#0B1526',
          900: '#050A13',
        },
        // Secondary Colors (Interactive Elements)
        secondary: {
          50: '#EBF8FF',
          100: '#BEE3F8',
          200: '#90CDF4',
          300: '#63B3ED',
          400: '#4299E1',
          500: '#2C5282', // Corporate Blue
          600: '#2A4365',
          700: '#1A365D',
          800: '#153E75',
          900: '#1A202C',
        },
        // Risk Level Colors
        risk: {
          critical: '#DC2626',
          high: '#EA580C',
          medium: '#CA8A04',
          low: '#16A34A',
          clear: '#0D9488',
        },
        // Semantic Colors
        success: {
          DEFAULT: '#059669',
          bg: '#ECFDF5',
        },
        warning: {
          DEFAULT: '#D97706',
          bg: '#FFFBEB',
        },
        error: {
          DEFAULT: '#DC2626',
          bg: '#FEF2F2',
        },
        info: {
          DEFAULT: '#0284C7',
          bg: '#F0F9FF',
        },
        // Neutral Colors
        neutral: {
          0: '#FFFFFF',
          50: '#F9FAFB',
          100: '#F3F4F6',
          200: '#E5E7EB',
          300: '#D1D5DB',
          400: '#9CA3AF',
          500: '#6B7280',
          600: '#4B5563',
          700: '#374151',
          800: '#1F2937',
          900: '#111827',
          950: '#030712',
        },
      },
      fontFamily: {
        display: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        body: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      fontSize: {
        'display-2xl': ['4.5rem', { lineHeight: '1' }],
        'display-xl': ['3.75rem', { lineHeight: '1' }],
        'display-lg': ['3rem', { lineHeight: '1.1' }],
        'display-md': ['2.25rem', { lineHeight: '1.2' }],
        'display-sm': ['1.875rem', { lineHeight: '1.3' }],
        'heading-xl': ['1.5rem', { lineHeight: '1.25' }],
        'heading-lg': ['1.25rem', { lineHeight: '1.3' }],
        'heading-md': ['1.125rem', { lineHeight: '1.4' }],
        'heading-sm': ['1rem', { lineHeight: '1.5' }],
        'heading-xs': ['0.875rem', { lineHeight: '1.5' }],
        'body-lg': ['1.125rem', { lineHeight: '1.625' }],
        'body-md': ['1rem', { lineHeight: '1.5' }],
        'body-sm': ['0.875rem', { lineHeight: '1.5' }],
        'body-xs': ['0.75rem', { lineHeight: '1.5' }],
        caption: ['0.75rem', { lineHeight: '1.5' }],
        overline: ['0.625rem', { lineHeight: '1.5' }],
      },
      borderRadius: {
        DEFAULT: '0.25rem',
        sm: '0.125rem',
        md: '0.375rem',
        lg: '0.5rem',
        xl: '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      boxShadow: {
        xs: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        sm: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
        '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
        inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
        primary: '0 4px 14px 0 rgb(26 54 93 / 0.15)',
        danger: '0 4px 14px 0 rgb(220 38 38 / 0.15)',
        success: '0 4px 14px 0 rgb(5 150 105 / 0.15)',
      },
      zIndex: {
        base: '0',
        dropdown: '1000',
        sticky: '1100',
        fixed: '1200',
        backdrop: '1300',
        modal: '1400',
        popover: '1500',
        tooltip: '1600',
        toast: '1700',
      },
      transitionDuration: {
        instant: '0ms',
        fast: '100ms',
        normal: '200ms',
        slow: '300ms',
        slower: '500ms',
      },
      animation: {
        'fade-in': 'fadeIn 200ms ease-out',
        'slide-in': 'slideIn 300ms ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}

export default config
