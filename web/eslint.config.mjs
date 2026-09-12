import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";

export default defineConfig([
  ...nextVitals,
  {
    // App Router's root layout owns the font stylesheet for every route.
    files: ["app/layout.js"],
    rules: { "@next/next/no-page-custom-font": "off" },
  },
  globalIgnores([".next/**", "out/**", "node_modules/**"]),
]);
