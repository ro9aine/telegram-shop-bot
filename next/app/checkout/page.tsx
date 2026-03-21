"use client";

import Link from "next/link";
import { Button } from "antd";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { BasketItem, basketTotal, checkoutBasket, fetchBasket } from "../../lib/basket";

export default function CheckoutPage() {
  const router = useRouter();
  const [items, setItems] = useState<BasketItem[]>([]);
  const [recipientName, setRecipientName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [deliveryComment, setDeliveryComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const sync = async () => setItems(await fetchBasket());
    void sync();
  }, []);

  const total = useMemo(() => basketTotal(items), [items]);
  const canCheckout =
    items.length > 0 &&
    recipientName.trim().length > 0 &&
    phoneNumber.trim().length > 0 &&
    deliveryAddress.trim().length > 0 &&
    !submitting;

  const submitOrder = useCallback(async () => {
    if (!canCheckout) {
      return;
    }

    const webApp = window.Telegram?.WebApp;
    const mainButton = webApp?.MainButton;
    setSubmitting(true);
    mainButton?.showProgress(true);

    try {
      const order = await checkoutBasket({
        recipient_name: recipientName.trim(),
        phone_number: phoneNumber.trim(),
        delivery_address: deliveryAddress.trim(),
        delivery_comment: deliveryComment.trim(),
      });

      if (!order) {
        webApp?.showAlert?.("Unable to create order. Please try again.");
        return;
      }

      webApp?.showAlert?.(`Order #${order.id} created successfully.`);
      router.push("/basket");
    } finally {
      mainButton?.hideProgress();
      setSubmitting(false);
    }
  }, [canCheckout, deliveryAddress, deliveryComment, phoneNumber, recipientName, router]);

  useEffect(() => {
    const webApp = window.Telegram?.WebApp;
    const mainButton = webApp?.MainButton;
    if (!webApp || !mainButton) {
      return;
    }

    const onMainButtonClick = () => {
      void submitOrder();
    };

    webApp.onEvent?.("mainButtonClicked", onMainButtonClick);
    return () => webApp.offEvent?.("mainButtonClicked", onMainButtonClick);
  }, [submitOrder]);

  useEffect(() => {
    const mainButton = window.Telegram?.WebApp?.MainButton;
    if (!mainButton) {
      return;
    }

    mainButton.setText(submitting ? "Submitting..." : "Подтвердить заказ");
    mainButton.show();
    if (canCheckout) {
      mainButton.enable();
    } else {
      mainButton.disable();
    }
    return () => mainButton.hide();
  }, [canCheckout, submitting]);

  if (!items.length) {
    return (
      <main className="page">
        <header className="hero">
          <h1>Checkout</h1>
          <p>Your basket is empty.</p>
        </header>
        <section className="basket-empty">
          <Link className="chip chip-active" href="/basket">
            Back to basket
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="hero">
        <h1>Checkout</h1>
        <p>Total: {total.toFixed(2)}</p>
      </header>

      <section className="checkout-card">
        <h2>Delivery details</h2>
        <div className="checkout-field">
          <label htmlFor="checkout-name">Recipient name</label>
          <input
            id="checkout-name"
            onChange={(event) => setRecipientName(event.target.value)}
            placeholder="John Doe"
            type="text"
            value={recipientName}
          />
        </div>
        <div className="checkout-field">
          <label htmlFor="checkout-phone">Phone number</label>
          <input
            id="checkout-phone"
            onChange={(event) => setPhoneNumber(event.target.value)}
            placeholder="+1 555 123 4567"
            type="tel"
            value={phoneNumber}
          />
        </div>
        <div className="checkout-field">
          <label htmlFor="checkout-address">Delivery address</label>
          <textarea
            id="checkout-address"
            onChange={(event) => setDeliveryAddress(event.target.value)}
            placeholder="Street, building, apartment, floor"
            rows={3}
            value={deliveryAddress}
          />
        </div>
        <div className="checkout-field">
          <label htmlFor="checkout-comment">Comment</label>
          <textarea
            id="checkout-comment"
            onChange={(event) => setDeliveryComment(event.target.value)}
            placeholder="Optional comment for courier"
            rows={2}
            value={deliveryComment}
          />
        </div>
        <Button disabled={!canCheckout} loading={submitting} onClick={() => void submitOrder()} type="primary">
          Confirm order
        </Button>
      </section>
    </main>
  );
}
