/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        mfs: {
          bKash: "#E2136E",
          nagad: "#F7941D",
          rocket: "#8C3494",
        },
      },
    },
  },
  plugins: [],
};
