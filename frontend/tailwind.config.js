/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          50: "#F0F4F8",
          100: "#D9E2EC",
          200: "#BCCCDC",
          300: "#9FB3C8",
          400: "#829AB1",
          500: "#627D98",
          600: "#1E4D9F",
          700: "#153A7A",
          800: "#0F2B5C",
          850: "#0D234C",
          900: "#0A1C3C",
          950: "#061325",
        },
        upay: {
          400: "#FFD338",
          500: "#FFC709",
          600: "#E5B100",
          accent: "#FFC709",
          yellow: "#FFC709",
          "yellow-hover": "#E5B100",
          "yellow-light": "#FFF7D6",
          navy: "#0A1C3C",
          dark: "#070D18",
        },
        onyx: "#070D18",
        mfs: {
          upay: "#FFC709",
          bKash: "#E2136E",
          nagad: "#F7941D",
          rocket: "#8C3494",
        },
      },
      boxShadow: {
        "upay-glow": "0 0 25px -4px rgba(255, 199, 9, 0.35)",
        "upay-glow-lg": "0 0 50px -5px rgba(255, 199, 9, 0.45)",
        "navy-glow": "0 15px 35px -10px rgba(10, 28, 60, 0.6)",
        "glass": "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
        "glass-sm": "0 4px 16px 0 rgba(0, 0, 0, 0.25)",
      },
      backdropBlur: {
        xs: "2px",
      },
      animation: {
        "pulse-subtle": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "float": "float 5s ease-in-out infinite",
        "float-slow": "float 8s ease-in-out infinite",
        "shimmer": "shimmer 2.5s linear infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};
