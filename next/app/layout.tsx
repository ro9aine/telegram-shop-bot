import type { Metadata } from "next";
import React from "react";
import Script from "next/script";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import "antd/dist/reset.css";
import "./globals.css";
import AntdReact19Patch from "./components/antd-react19-patch";
import BottomNav from "./components/bottom-nav";

export const metadata: Metadata = {
  title: "Telegram Shop WebApp",
  description: "WebApp scaffold",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Script src="https://telegram.org/js/telegram-web-app.js" strategy="afterInteractive" />
        <AntdReact19Patch />
        <AntdRegistry>
          {children}
          <BottomNav />
        </AntdRegistry>
      </body>
    </html>
  );
}
