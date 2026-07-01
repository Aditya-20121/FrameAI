import type { NextConfig } from "next";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const ContentSecurityPolicy = `
  default-src 'self';
  script-src 'self' 'unsafe-inline' 'unsafe-eval';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: blob: https://r2.frameai.in https://*.r2.cloudflarestorage.com https://*.amazonaws.com;
  font-src 'self' https://fonts.gstatic.com;
  connect-src 'self' ${API} https://api.segmind.com https://tfhub.dev https://www.kaggle.com https://storage.googleapis.com;
  frame-ancestors 'none';
  object-src 'none';
  base-uri 'self';
`.replace(/\n/g, " ").trim();

const securityHeaders = [
  { key: "X-DNS-Prefetch-Control",      value: "on" },
  { key: "X-Frame-Options",             value: "DENY" },
  { key: "X-Content-Type-Options",      value: "nosniff" },
  { key: "X-XSS-Protection",            value: "1; mode=block" },
  { key: "Referrer-Policy",             value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy",          value: "camera=self, microphone=(), geolocation=()" },
  { key: "Content-Security-Policy",     value: ContentSecurityPolicy },
];

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "r2.frameai.in",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "*.r2.cloudflarestorage.com",
        pathname: "/**",
      },
    ],
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
