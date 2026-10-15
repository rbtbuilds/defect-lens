import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5111,
    strictPort: true,
    proxy: {
      "/api": "http://127.0.0.1:8111",
      "/readyz": "http://127.0.0.1:8111",
      "/healthz": "http://127.0.0.1:8111",
    },
  },
});
