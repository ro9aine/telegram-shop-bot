"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { DeleteOutlined, LoadingOutlined, ShopOutlined, SmileOutlined } from "@ant-design/icons";
import { useEffect, useState } from "react";

function itemClass(pathname: string, href: string): string {
  const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
  return active ? "bottom-nav-item bottom-nav-item-active" : "bottom-nav-item";
}

export default function BottomNav() {
  const pathname = usePathname();
  const [activePath, setActivePath] = useState("");
  const [loadingPath, setLoadingPath] = useState<string | null>(null);

  useEffect(() => {
    setActivePath(pathname);
    setLoadingPath(null);
  }, [pathname]);

  useEffect(() => {
    if (!loadingPath) {
      return;
    }
    const timer = setTimeout(() => setLoadingPath(null), 2500);
    return () => clearTimeout(timer);
  }, [loadingPath]);

  function activate(path: string): void {
    if (path === pathname) {
      return;
    }
    setLoadingPath(path);
    setActivePath(path);
  }

  return (
    <nav className="bottom-nav" role="navigation" aria-label="Main navigation">
      <Link
        aria-label="Catalog"
        className={itemClass(activePath, "/")}
        href="/"
        onClick={() => activate("/")}
        title="Catalog"
      >
        {loadingPath === "/" ? <LoadingOutlined spin /> : <ShopOutlined />}
      </Link>
      <Link
        aria-label="Basket"
        className={itemClass(activePath, "/basket")}
        href="/basket"
        onClick={() => activate("/basket")}
        title="Basket"
      >
        {loadingPath === "/basket" ? <LoadingOutlined spin /> : <DeleteOutlined />}
      </Link>
      <Link
        aria-label="Profile"
        className={itemClass(activePath, "/profile")}
        href="/profile"
        onClick={() => activate("/profile")}
        title="Profile"
      >
        {loadingPath === "/profile" ? <LoadingOutlined spin /> : <SmileOutlined />}
      </Link>
    </nav>
  );
}
