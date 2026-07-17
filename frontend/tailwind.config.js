/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        twin: {
          bg: "#0b1120",
          panel: "#111827",
          accent: "#3b82f6",
        },
      },
    },
  },
  plugins: [],
};
