import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// GitHub Pages serves a project repo from /<repo>/, so the base path must
// match. Set VITE_BASE=/thread-of-life/ when building for Pages, or leave it
// unset for local dev and root deployments.
export default defineConfig({
  base: process.env.VITE_BASE || "/",
  plugins: [react()],
  server: { host: true, port: 5173 },
});
