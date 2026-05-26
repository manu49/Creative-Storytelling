import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
};

export default config;
