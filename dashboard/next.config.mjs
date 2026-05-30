/** @type {import('next').NextConfig} */
const nextConfig = {
  // The landing page is self-contained; lint is run separately in CI.
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
