/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Reports are loaded from ../reports at build time. On Vercel, the entire
  // repo is checked out, so this works for both dev and prod builds.
};

module.exports = nextConfig;
