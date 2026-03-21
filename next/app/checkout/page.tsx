"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { BasketItem, basketTotal, checkoutBasket, fetchBasket } from "../../lib/basket";
import { browserApi } from "../../lib/http";
import { useTelegramBackButton, useTelegramMainButton } from "../../lib/use-telegram-buttons";
import { useTelegramWebAppUser } from "../../lib/use-telegram-webapp-user";

type ProfilePayload = {
  profile?: {
    telegram_user_id: number;
    username: string;
    first_name: string;
    last_name: string;
    photo_url: string;
    phone_number: string;
  };
};

export default function CheckoutPage() {
  const router = useRouter();
  const [items, setItems] = useState<BasketItem[]>([]);
  const [recipientName, setRecipientName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [deliveryComment, setDeliveryComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [profile, setProfile] = useState<ProfilePayload["profile"] | null>(null);
  const telegramUser = useTelegramWebAppUser();

  useEffect(() => {
    const sync = async () => setItems(await fetchBasket());
    void sync();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    browserApi
      .get<ProfilePayload>("/profile/me/", { signal: controller.signal })
      .then((response) => {
        if (response.status >= 200 && response.status < 300) {
          setProfile(response.data.profile ?? null);
        } else {
          setProfile(null);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setProfile(null);
        }
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!recipientName.trim()) {
      const first = profile?.first_name || telegramUser?.firstName || "";
      const last = profile?.last_name || telegramUser?.lastName || "";
      const fullName = `${first} ${last}`.trim();
      if (fullName) {
        setRecipientName(fullName);
      }
    }

    if (!phoneNumber.trim()) {
      const nextPhone = (profile?.phone_number || "").trim();
      if (nextPhone) {
        setPhoneNumber(nextPhone);
      }
    }
  }, [
    phoneNumber,
    profile?.first_name,
    profile?.last_name,
    profile?.phone_number,
    recipientName,
    telegramUser?.firstName,
    telegramUser?.lastName,
  ]);

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

    setSubmitting(true);

    try {
      const order = await checkoutBasket({
        recipient_name: recipientName.trim(),
        phone_number: phoneNumber.trim(),
        delivery_address: deliveryAddress.trim(),
        delivery_comment: deliveryComment.trim(),
      });

      if (!order) {
        window.Telegram?.WebApp?.showAlert?.("Unable to create order. Please try again.");
        return;
      }

      window.Telegram?.WebApp?.showAlert?.(`Order #${order.id} created successfully.`);
      router.push(`/payment?orderId=${order.id}`);
    } finally {
      setSubmitting(false);
    }
  }, [canCheckout, deliveryAddress, deliveryComment, phoneNumber, recipientName, router]);

  useTelegramBackButton(() => router.push("/basket"), true);
  useTelegramMainButton({
    text: submitting ? "Submitting..." : "Confirm order",
    enabled: canCheckout,
    loading: submitting,
    visible: true,
    onClick: () => {
      void submitOrder();
    },
  });

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
      </section>
    </main>
  );
}

