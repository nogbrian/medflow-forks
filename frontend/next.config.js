/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: {
    // Enable server actions
  },
  // API rewrites to backend
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: process.env.API_URL || "http://localhost:8000/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
