/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "-apple-system", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
        display: ["var(--font-sans)", "sans-serif"],
      },
      letterSpacing: {
        tighter: "-0.035em",
        tight: "-0.02em",
        normal: "-0.005em",
        wide: "0.05em",
        wider: "0.12em",
        widest: "0.20em",
      },
      colors: {
        navy: {
          50: "#F8FAFC",
          100: "#F1F5F9",
          200: "#E2E8F0",
          300: "#CBD5E1",
          400: "#94A3B8",
          500: "#64748B",
          600: "#475569",
          700: "#334155",
          800: "#1E293B",
          850: "#172033",
          900: "#0F172A",
          950: "#020617",
        },
        upay: {
          400: "#FFD338",
          500: "#FFC709",
          600: "#E5B100",
          accent: "#FFC709",
          yellow: "#FFC709",
          "yellow-hover": "#E5B100",
          "yellow-light": "#FFF7D6",
          navy: "#0F172A",
          dark: "#020617",
        },
        onyx: "#020617",
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
      borderRadius: {
        "4xl": "2rem",
        "5xl": "2.5rem",
      },
      transitionTimingFunction: {
        premium: "cubic-bezier(0.16, 1, 0.3, 1)",
      },
      animation: {
        "pulse-subtle": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "float": "float 5s ease-in-out infinite",
        "float-slow": "float 8s ease-in-out infinite",
        "shimmer": "shimmer 2.5s linear infinite",
        "fade-in-up": "fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-in-right": "slideInRight 0.5s ease-out forwards",
        "scale-in": "fadeInScale 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "glow-pulse": "glowPulse 3s ease-in-out infinite",
        "border-beam": "borderBeam calc(var(--duration)*1s) infinite linear",
      },
      keyframes: {
        borderBeam: {
          "100%": {
            "offset-distance": "100%",
          },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        fadeInUp: {
          from: { opacity: "0", transform: "translateY(24px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        fadeInScale: {
          from: { opacity: "0", transform: "scale(0.95) translateY(12px)" },
          to: { opacity: "1", transform: "scale(1) translateY(0)" },
        },
        slideInRight: {
          from: { opacity: "0", transform: "translateX(24px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        glowPulse: {
          "0%, 100%": { opacity: "0.5", transform: "scale(1)" },
          "50%": { opacity: "1", transform: "scale(1.05)" },
        },
      },
    },
  },
  plugins: [],
};
