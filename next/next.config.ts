import type { NextConfig } from "next";

const envOrigins =
  process.env.NEXT_ALLOWED_DEV_ORIGINS?.split(",")
    .map((origin) => origin.trim())
    .filter(Boolean) ?? [];

const nextConfig: NextConfig = {
  allowedDevOrigins: ["*.ngrok-free.app", ...envOrigins],
};

export default nextConfig;
