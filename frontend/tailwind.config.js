/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#12263A",
        coral: "#FF6B35",
        mint: "#2EC4B6",
        paper: "#FFF7E8"
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Manrope", "sans-serif"]
      },
      boxShadow: {
        panel: "0 20px 40px rgba(18, 38, 58, 0.16)"
      }
    }
  },
  plugins: []
};
