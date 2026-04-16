/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/portal/**/*.html"],
  theme: {
    extend: {
      colors: {
        primary: "#8B4513",
        accent: "#D2691E",
        success: "#16A34A",
        warning: "#F59E0B",
        error: "#DC2626",
        surface: "#FBF8F3",
        surfaceLight: "#FFFBF5",
        textPrimary: "#1F2937",
        textSecondary: "#6B7280",
        textTertiary: "#9CA3AF",
        border: "#E5E7EB",
        borderLight: "#F3F4F6",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
