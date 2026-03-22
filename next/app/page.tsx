"use client";

import { Badge, Button } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { addToBasket, BasketItem, fetchBasket, removeFromBasket } from "../lib/basket";
import { browserApi } from "../lib/http";

type Product = {
  id: number;
  title: string;
  price: string;
  images: string[];
};

type ProductsPayload = {
  items: Product[];
  pagination: {
    page: number;
    total_pages: number;
  };
};

export default function HomePage() {
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [basketQuantities, setBasketQuantities] = useState<Record<number, number>>({});
  const [basketLoadingById, setBasketLoadingById] = useState<Record<number, boolean>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [navigatingToId, setNavigatingToId] = useState<number | null>(null);

  const applyBasketItems = (items: BasketItem[]) => {
    const next: Record<number, number> = {};
    for (const item of items) {
      next[item.productId] = item.quantity;
    }
    setBasketQuantities(next);
  };

  useEffect(() => {
    const controller = new AbortController();
    setIsLoading(true);

    fetchBasket()
      .then((items) => applyBasketItems(items))
      .catch(() => applyBasketItems([]));

    browserApi
      .get<ProductsPayload>("/catalog/products/?page=1&page_size=12", {
        signal: controller.signal,
      })
      .then((response) => {
        if (response.status >= 200 && response.status < 300) {
          setProducts(response.data.items ?? []);
        } else {
          setProducts([]);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setProducts([]);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const sync = async () => applyBasketItems(await fetchBasket());
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

  return (
    <main className="page">
      <header className="hero">
        <h1>Catalog</h1>
      </header>

      <section className="grid">
        {isLoading
          ? Array.from({ length: 12 }).map((_, idx) => (
              <article
                className="card catalog-skeleton-card"
                key={`skeleton-${idx}`}
              >
                <div className="catalog-skeleton-image" />
                <div className="catalog-skeleton-content">
                  <div className="catalog-skeleton-line catalog-skeleton-line-title" />
                  <div className="catalog-skeleton-line catalog-skeleton-line-price" />
                </div>
              </article>
            ))
          : products.map((item) => {
              const isNavigating = navigatingToId === item.id;
              const quantityInBasket = basketQuantities[item.id] ?? 0;
              const isBasketUpdating = basketLoadingById[item.id] === true;
              return (
                <article className="card" key={item.id}>
                  <Link
                    className={
                      isNavigating
                        ? "card-clickable card-loading"
                        : "card-clickable"
                    }
                    href={`/product/${item.id}`}
                    onClick={() => setNavigatingToId(item.id)}
                    onMouseEnter={() => router.prefetch(`/product/${item.id}`)}
                    prefetch
                  >
                    {item.images[0] ? (
                      <img
                        alt={item.title}
                        className="card-image"
                        src={item.images[0]}
                      />
                    ) : null}
                    <h2 title={item.title}>{item.title}</h2>
                    {isNavigating ? (
                      <div className="card-loading-overlay" aria-hidden="true" />
                    ) : null}
                  </Link>
                  <div className="catalog-card-footer">
                    <div className="catalog-price-inline">{item.price}</div>
                    <Badge count={quantityInBasket > 0 ? 1 : 0} size="small">
                      <Button
                        aria-label={
                          quantityInBasket > 0
                            ? `Remove ${item.title} from basket`
                            : `Add ${item.title} to basket`
                        }
                        className="catalog-add-btn"
                        onClick={async () => {
                          if (isBasketUpdating) {
                            return;
                          }
                          setBasketLoadingById((prev) => ({ ...prev, [item.id]: true }));
                          try {
                            if (quantityInBasket > 0) {
                              applyBasketItems(await removeFromBasket(item.id));
                              return;
                            }
                            const items = await addToBasket({
                              productId: item.id,
                              title: item.title,
                              price: item.price,
                              image: item.images[0] ?? null,
                            });
                            applyBasketItems(items);
                          } finally {
                            setBasketLoadingById((prev) => ({ ...prev, [item.id]: false }));
                          }
                        }}
                        loading={isBasketUpdating}
                        size="small"
                        type={quantityInBasket > 0 ? "default" : "primary"}
                        icon={<DeleteOutlined />}
                      />
                    </Badge>
                  </div>
                </article>
              );
            })}
      </section>
    </main>
  );
}
