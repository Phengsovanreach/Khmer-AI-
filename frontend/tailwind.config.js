/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#10141c',
        panel: '#171d28',
        gold: '#d9b56d',
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans Khmer', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        heading: ['Manrope', 'Noto Sans Khmer', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        display: ['Space Grotesk', 'Manrope', 'Noto Sans Khmer', 'sans-serif'],
        khmer: ['Noto Sans Khmer', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'SF Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
};
