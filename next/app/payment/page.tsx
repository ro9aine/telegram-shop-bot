"use client";

import Link from "next/link";
import { Button } from "antd";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo, useState } from "react";

import { markOrderPaid } from "../../lib/basket";
import { useTelegramBackButton, useTelegramMainButton } from "../../lib/use-telegram-buttons";

export default function PaymentPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [submitting, setSubmitting] = useState(false);
  const [paid, setPaid] = useState(false);

  const orderId = useMemo(() => {
    const raw = (searchParams.get("orderId") || "").trim();
    const value = Number.parseInt(raw, 10);
    if (!Number.isFinite(value) || value <= 0) {
      return null;
    }
    return value;
  }, [searchParams]);

  const submitPaid = useCallback(async () => {
    if (submitting || paid || !orderId) {
      return;
    }
    setSubmitting(true);
    try {
      const result = await markOrderPaid(orderId);
      if (!result) {
        window.Telegram?.WebApp?.showAlert?.("Unable to mark payment. Please try again.");
        return;
      }
      setPaid(true);
      window.Telegram?.WebApp?.showAlert?.(`Payment for order #${result.id} is marked.`);
      router.push("/profile");
    } finally {
      setSubmitting(false);
    }
  }, [orderId, paid, router, submitting]);

  useTelegramBackButton(() => router.push("/profile"), true);
  useTelegramMainButton({
    text: submitting ? "Submitting..." : "I paid for this order",
    enabled: Boolean(orderId) && !submitting && !paid,
    loading: submitting,
    visible: Boolean(orderId),
    onClick: () => {
      void submitPaid();
    },
  });

  if (!orderId) {
    return (
      <main className="page">
        <header className="hero">
          <h1>Payment</h1>
          <p>Order ID is missing.</p>
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
        <h1>Payment</h1>
        <p>Order #{orderId}</p>
      </header>

      <section className="checkout-card">
        <h2>Confirm payment</h2>
        <p>After you complete the payment, press the button below.</p>
        <Button disabled={submitting || paid} loading={submitting} onClick={() => void submitPaid()} type="primary">
          I paid for this order
        </Button>
      </section>
    </main>
  );
}

