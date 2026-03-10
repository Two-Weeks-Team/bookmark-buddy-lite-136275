/**
 * Tailwind CSS configuration
 * This file replaces the TypeScript version (tailwind.config.ts) to ensure compatibility
 * with the Next.js build process, which expects a JavaScript configuration file.
 */
module.exports = {
  content: [
    './web/src/**/*.{js,ts,jsx,tsx,mdx}'
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};