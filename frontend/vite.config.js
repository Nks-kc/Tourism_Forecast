import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
  },
  server: {
    port: 5173,
    proxy: {
      "/auth":         "http://127.0.0.1:5000",
      "/health":       "http://127.0.0.1:5000",
      "/history":      "http://127.0.0.1:5000",
      "/predict":      "http://127.0.0.1:5000",
      "/evaluate":     "http://127.0.0.1:5000",
      "/compare":      "http://127.0.0.1:5000",
      "/countries":    "http://127.0.0.1:5000",
      "/admin":        "http://127.0.0.1:5000",
      "/watchlist":    "http://127.0.0.1:5000",
      "/reports":      "http://127.0.0.1:5000",
      "/notifications": "http://127.0.0.1:5000",
      "/preferences":  "http://127.0.0.1:5000",
    }
  }
});


