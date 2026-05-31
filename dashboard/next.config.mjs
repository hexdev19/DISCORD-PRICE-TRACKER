/** @type {import('next').NextConfig} */
const nextConfig = {
  // The landing page is self-contained; lint is run separately in CI.
  eslint: { ignoreDuringBuilds: true },
  // Required for the Docker image (copies only the necessary output).
  output: "standalone",
};

export default nextConfig;
