/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'picsum.photos' },
      { protocol: 'https', hostname: 'images.unsplash.com' },
      { protocol: 'https', hostname: 'r2.cloudflare.com' },
      { protocol: 'https', hostname: '*.s3.amazonaws.com' },
    ],
  },
};

module.exports = nextConfig;
