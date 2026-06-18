/** @type {import('next').NextConfig} */
const nextConfig = {
  // 'standalone' bundles only what's needed for production — required for Docker
  output: "standalone",
};

export default nextConfig;
