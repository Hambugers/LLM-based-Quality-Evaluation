/// <reference types="vitest" />

import { defineConfig, type UserConfig } from "vite";
import react from "@vitejs/plugin-react";

const config: UserConfig & {
  test: {
    environment: string;
    globals: boolean;
    setupFiles: string;
  };
} = {
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/sample-assets": "http://127.0.0.1:8001",
      "/uploads": "http://127.0.0.1:8001",
    },
  },
};

export default defineConfig(config);
