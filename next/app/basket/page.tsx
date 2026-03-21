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

  useEffect(() => {
    const webApp = window.Telegram?.WebApp;
    const mainButton = webApp?.MainButton;
    if (!webApp || !mainButton) {
      return;
    }

    const onMainButtonClick = () => {
      if (items.length > 0) {
        router.push("/checkout");
      }
    };

    webApp.onEvent?.("mainButtonClicked", onMainButtonClick);
    return () => webApp.offEvent?.("mainButtonClicked", onMainButtonClick);
  }, [items.length, router]);

  useEffect(() => {
    const mainButton = window.Telegram?.WebApp?.MainButton;
    if (!mainButton) {
      return;
    }

    if (!items.length) {
      mainButton.hide();
      return;
    }

    mainButton.setText(`К оформлению ${total.toFixed(2)}`);
    mainButton.show();
    mainButton.enable();
    return () => mainButton.hide();
  }, [items.length, total]);

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
                    onClick={async () => setItems(await updateBasketQuantity(item.productId, item.quantity - 1))}
                    size="small"
                    type="default"
                  >
                    -
                  </Button>
                  <span className="basket-item-qty">{item.quantity}</span>
                  <Button
                    onClick={async () => setItems(await updateBasketQuantity(item.productId, item.quantity + 1))}
                    size="small"
                    type="default"
                  >
                    +
                  </Button>
                  <Button
                    danger
                    onClick={async () => setItems(await removeFromBasket(item.productId))}
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
              onClick={async () => setItems(await clearBasket())}
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
