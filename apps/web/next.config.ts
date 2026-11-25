import type { NextConfig } from "next";

// One .env at the repo root is shared by the web app, the agent and gen-items.
// Variables already set in the shell win over the file.
try {
  process.loadEnvFile(new URL("../../.env", import.meta.url));
} catch {
  // No root .env (for example on Vercel, where variables are set in the dashboard).
}

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  partialPrefetching: true,
};

export default nextConfig;
