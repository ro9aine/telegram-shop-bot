"use client";

import Link from "next/link";
import { Button } from "antd";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  BasketItem,
  basketTotal,
  clearBasket,
  fetchBasket,
  removeFromBasket,
  updateBasketQuantity,
} from "../../lib/basket";
import { useTelegramMainButton } from "../../lib/use-telegram-buttons";

export default function BasketPage() {
  const router = useRouter();
  const [items, setItems] = useState<BasketItem[]>([]);

  useEffect(() => {
    const sync = async () => setItems(await fetchBasket());
    void sync();

    const onBasketChanged = (event: Event) => {
      const custom = event as CustomEvent<BasketItem[]>;
      if (Array.isArray(custom.detail)) {
        setItems(custom.detail);
        return;
      }
      void sync();
    };

    window.addEventListener("basket:changed", onBasketChanged);
    return () => window.removeEventListener("basket:changed", onBasketChanged);
  }, []);

  const total = useMemo(() => basketTotal(items), [items]);

  useTelegramMainButton({
    text: `Proceed to checkout ${total.toFixed(2)}`,
    enabled: items.length > 0,
    visible: items.length > 0,
    onClick: () => {
      if (items.length > 0) {
        router.push("/checkout");
      }
    },
  });

  return (
    <main className="page">
      <header className="hero">
        <h1>Basket</h1>
        <p>{items.length ? "Your selected products." : "Basket is empty."}</p>
      </header>

      {!items.length ? (
        <section className="basket-empty">
          <p>Add products from catalog to see them here.</p>
          <Link className="chip chip-active" href="/">
            Go to catalog
          </Link>
        </section>
      ) : (
        <section className="basket-list">
          {items.map((item) => (
            <article className="basket-item" key={item.productId}>
              <Link className="basket-item-link" href={`/product/${item.productId}`}>
                {item.image ? <img alt={item.title} className="basket-item-image" src={item.image} /> : <div className="basket-item-image" />}
              </Link>
              <div className="basket-item-content">
                <Link className="basket-item-title" href={`/product/${item.productId}`}>
                  {item.title}
                </Link>
                <div className="basket-item-price">{item.price}</div>
                <div className="basket-item-controls">
                  <Button
                    onClick={async () => {
                      const next = await updateBasketQuantity(item.productId, item.quantity - 1);
                      setItems(next);
                    }}
                    size="small"
                    type="default"
                  >
                    -
                  </Button>
                  <span className="basket-item-qty">{item.quantity}</span>
                  <Button
                    onClick={async () => {
                      const next = await updateBasketQuantity(item.productId, item.quantity + 1);
                      setItems(next);
                    }}
                    size="small"
                    type="default"
                  >
                    +
                  </Button>
                  <Button
                    danger
                    onClick={async () => {
                      const next = await removeFromBasket(item.productId);
                      setItems(next);
                    }}
                    size="small"
                    type="text"
                  >
                    Remove
                  </Button>
                </div>
              </div>
            </article>
          ))}

          <div className="basket-summary">
            <div className="basket-total">Total: {total.toFixed(2)}</div>
            <Button
              danger
              onClick={async () => {
                setItems(await clearBasket());
              }}
              type="default"
            >
              Clear basket
            </Button>
          </div>
        </section>
      )}
    </main>
  );
}

