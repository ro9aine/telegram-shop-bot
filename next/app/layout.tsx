import type { Metadata } from "next";
import "antd/dist/reset.css";
import "./globals.css";
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
    <html lang="en">
      <body>
        {children}
        <BottomNav />
      </body>
    </html>
  );
}
