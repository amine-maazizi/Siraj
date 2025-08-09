import { fontFamily } from "tailwindcss/defaultTheme";

export default {
  darkMode: ["class"],
  content: [
   "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        amberGlow: "#FFB454", // Primary
        indigoBg: "#2E1A47", // Background
        sandLight: "#F6E7CB", // Accent Light
        midnight: "#1A0E2E", // Accent Dark
        goldHi: "#FFC94A",   // Highlight
      },
      fontFamily: {
        sans: ["Inter", ...fontFamily.sans],
      },
      boxShadow: {
        soft: "0 8px 16px rgba(0,0,0,0.15)",
      }
    },
  },
  plugins: [],
};