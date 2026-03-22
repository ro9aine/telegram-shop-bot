"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { browserApi } from "../../lib/http";
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

type OrdersPayload = {
  orders?: Array<{
    id: number;
    status: string;
    payment_status: string;
    total_amount: string;
    items_count: number;
    created_at: string;
  }>;
};

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfilePayload["profile"] | null>(null);
  const [orders, setOrders] = useState<OrdersPayload["orders"]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);

    Promise.all([
      browserApi.get<ProfilePayload>("/profile/me/", { signal: controller.signal }),
      browserApi.get<OrdersPayload>("/orders/", { signal: controller.signal }),
    ])
      .then(([profileResponse, ordersResponse]) => {
        if (profileResponse.status >= 200 && profileResponse.status < 300) {
          setProfile(profileResponse.data.profile ?? null);
        } else {
          setProfile(null);
        }
        if (ordersResponse.status >= 200 && ordersResponse.status < 300) {
          setOrders(ordersResponse.data.orders ?? []);
        } else {
          setOrders([]);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setProfile(null);
          setOrders([]);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, []);

  const telegramUser = useTelegramWebAppUser();

  const firstName = profile?.first_name || telegramUser?.firstName || "-";
  const lastName = profile?.last_name || telegramUser?.lastName || "-";
  const photoUrl = profile?.photo_url || telegramUser?.photoUrl || "";

  if (loading) {
    return (
      <main className="page">
        <header className="hero">
          <h1>Profile</h1>
          <p>Loading profile...</p>
        </header>

        <section className="profile-card">
          <div className="profile-photo-wrap">
            <div className="profile-photo profile-photo-skeleton" />
          </div>

          <div className="profile-fields">
            {Array.from({ length: 4 }).map((_, idx) => (
              <div className="profile-field" key={`profile-skeleton-${idx}`}>
                <div className="catalog-skeleton-line profile-skeleton-label" />
                <div className="catalog-skeleton-line profile-skeleton-value" />
              </div>
            ))}
          </div>
        </section>

        <section className="profile-orders">
          <h2>Orders</h2>
          <div className="profile-orders-list">
            {Array.from({ length: 3 }).map((_, idx) => (
              <article className="profile-order-item" key={`order-skeleton-${idx}`}>
                <div className="profile-order-top">
                  <div className="catalog-skeleton-line profile-order-skeleton-id" />
                  <div className="catalog-skeleton-line profile-order-skeleton-date" />
                </div>
                <div className="profile-order-meta">
                  <div className="catalog-skeleton-line profile-order-skeleton-chip" />
                  <div className="catalog-skeleton-line profile-order-skeleton-chip" />
                  <div className="catalog-skeleton-line profile-order-skeleton-chip" />
                  <div className="catalog-skeleton-line profile-order-skeleton-chip" />
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="page">
      <header className="hero">
        <h1>Profile</h1>
        <p>Your personal data.</p>
      </header>

      <section className="profile-card">
        <div className="profile-photo-wrap">
          {photoUrl ? <img alt="Profile photo" className="profile-photo" src={photoUrl} /> : <div className="profile-photo profile-photo-empty">?</div>}
        </div>

        <div className="profile-fields">
          <div className="profile-field">
            <span className="profile-label">Name</span>
            <span className="profile-value">{firstName}</span>
          </div>
          <div className="profile-field">
            <span className="profile-label">Surname</span>
            <span className="profile-value">{lastName}</span>
          </div>
          <div className="profile-field">
            <span className="profile-label">Phone</span>
            <span className="profile-value">{profile?.phone_number || "-"}</span>
          </div>
          <div className="profile-field">
            <span className="profile-label">Username</span>
            <span className="profile-value">{profile?.username ? `@${profile.username}` : telegramUser?.username ? `@${telegramUser.username}` : "-"}</span>
          </div>
        </div>
      </section>

      <section className="profile-orders">
        <h2>Orders</h2>
        <div className="profile-order-actions" style={{ marginBottom: 10 }}>
          <Link className="chip chip-active" href="/notifications">
            Notifications
          </Link>
        </div>
        {!orders?.length ? (
          <p className="profile-orders-empty">No orders yet.</p>
        ) : (
          <div className="profile-orders-list">
            {orders.map((order) => (
              <article className="profile-order-item" key={order.id}>
                <div className="profile-order-top">
                  <span className="profile-order-id">#{order.id}</span>
                  <span className="profile-order-date">{new Date(order.created_at).toLocaleString()}</span>
                </div>
                <div className="profile-order-meta">
                  <span>Status: {order.status}</span>
                  <span>Payment: {order.payment_status}</span>
                  <span>Items: {order.items_count}</span>
                  <span>Total: {order.total_amount}</span>
                </div>
                {order.payment_status !== "paid" ? (
                  <div className="profile-order-actions">
                    <Link className="chip chip-active" href={`/payment?orderId=${order.id}`}>
                      Pay order
                    </Link>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
