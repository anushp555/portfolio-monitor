import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      colors: {
        ink: {
          900: "#0d0d0e",
          800: "#16161a",
          700: "#1f1f25",
          600: "#2b2b33",
          500: "#3a3a44",
        },
        bone: {
          50: "#f5f1e8",
          100: "#ebe6d8",
          200: "#d8d0bc",
          300: "#a8a190",
          400: "#797368",
        },
        signal: {
          emerald: "#5fa67a",  // catalyst_drove_move (story checks out)
          amber:   "#d4a64a",  // catalyst_without_move (lag opportunity)
          crimson: "#c45050",  // move_without_catalyst (anomaly)
          slate:   "#5a6168",  // no_signal
        },
      },
      letterSpacing: {
        tightest: "-0.04em",
      },
    },
  },
  plugins: [],
};

export default config;
