import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "r2.frameai.in",
        pathname: "/**",
      },
    ],
  },
};

export default nextConfig;
