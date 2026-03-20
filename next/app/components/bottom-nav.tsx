"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { DeleteOutlined, ShopOutlined, SmileOutlined } from "@ant-design/icons";

function itemClass(pathname: string, href: string): string {
  const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
  return active ? "bottom-nav-item bottom-nav-item-active" : "bottom-nav-item";
}

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="bottom-nav" role="navigation" aria-label="Main navigation">
      <Link aria-label="Catalog" className={itemClass(pathname, "/")} href="/" title="Catalog">
        <ShopOutlined />
      </Link>
      <Link aria-label="Basket" className={itemClass(pathname, "/basket")} href="/basket" title="Basket">
        <DeleteOutlined />
      </Link>
      <Link aria-label="Profile" className={itemClass(pathname, "/profile")} href="/profile" title="Profile">
        <SmileOutlined />
      </Link>
    </nav>
  );
}
