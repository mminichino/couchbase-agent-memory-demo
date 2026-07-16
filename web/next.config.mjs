/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: {
    typedRoutes: true,
    serverComponentsExternalPackages: ["couchbase"]
  }
};

export default nextConfig;
