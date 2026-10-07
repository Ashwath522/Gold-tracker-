import type { NextConfig } from "next";

function getBackendUrl() {
  const raw = (process.env.BACKEND_URL ?? "").trim();
  if (!raw) return "http://127.0.0.1:8000";
  const withProtocol = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
  return withProtocol.replace(/\/+$/, "");
}

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${getBackendUrl()}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
