"use client";

import { Badge } from "antd";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { DeleteOutlined, LoadingOutlined, ShopOutlined, SmileOutlined } from "@ant-design/icons";
import { useEffect, useState } from "react";
import { BasketItem, fetchBasket } from "../../lib/basket";

function itemClass(pathname: string, href: string): string {
  const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
  return active ? "bottom-nav-item bottom-nav-item-active" : "bottom-nav-item";
}

export default function BottomNav() {
  const pathname = usePathname();
  const [activePath, setActivePath] = useState("");
  const [loadingPath, setLoadingPath] = useState<string | null>(null);
  const [basketCount, setBasketCount] = useState(0);
  const isBasketActive = activePath.startsWith("/basket");
  const basketIconColor = isBasketActive ? "var(--accent)" : "var(--muted)";

  const applyBasketItems = (items: BasketItem[]) => {
    setBasketCount(items.reduce((sum, item) => sum + item.quantity, 0));
  };

  useEffect(() => {
    setActivePath(pathname);
    setLoadingPath(null);
  }, [pathname]);

  useEffect(() => {
    const sync = async () => applyBasketItems(await fetchBasket());
    void sync();

    const onBasketChanged = (event: Event) => {
      const custom = event as CustomEvent<BasketItem[]>;
      if (Array.isArray(custom.detail)) {
        applyBasketItems(custom.detail);
        return;
      }
      void sync();
    };

    window.addEventListener("basket:changed", onBasketChanged);
    return () => window.removeEventListener("basket:changed", onBasketChanged);
  }, []);

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
        <Badge className="bottom-nav-badge" count={basketCount} overflowCount={99} offset={[6, 1]}>
          <span className="bottom-nav-basket-icon">
            {loadingPath === "/basket" ? (
              <LoadingOutlined spin style={{ color: basketIconColor, fontSize: 34 }} />
            ) : (
              <DeleteOutlined style={{ color: basketIconColor, fontSize: 34 }} />
            )}
          </span>
        </Badge>
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
