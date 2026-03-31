/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../app/templates/**/*.html",
    "../static/js/**/*.js",
    "./src/**/*.{html,js}",
  ],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["light", "dark", "corporate"],
    defaultTheme: "light",
    logs: false,
  },
};
