"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchNotifications, markNotificationsRead, type UserNotification } from "../../lib/notifications";

export default function NotificationsPage() {
  const [items, setItems] = useState<UserNotification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let disposed = false;

    const load = async () => {
      setLoading(true);
      const payload = await fetchNotifications(false);
      if (!disposed) {
        setItems(payload.items);
        setLoading(false);
      }
      await markNotificationsRead();
    };

    void load();
    return () => {
      disposed = true;
    };
  }, []);

  return (
    <main className="page">
      <header className="hero">
        <h1>Notifications</h1>
        <p>Order updates and system messages.</p>
      </header>

      {loading ? (
        <section className="profile-orders">
          <div className="profile-orders-list">
            {Array.from({ length: 4 }).map((_, idx) => (
              <article className="profile-order-item" key={`notification-skeleton-${idx}`}>
                <div className="catalog-skeleton-line profile-order-skeleton-id" />
                <div className="catalog-skeleton-line profile-order-skeleton-date" />
              </article>
            ))}
          </div>
        </section>
      ) : !items.length ? (
        <section className="basket-empty">
          <p>No notifications yet.</p>
          <Link className="chip chip-active" href="/profile">
            Back to profile
          </Link>
        </section>
      ) : (
        <section className="profile-orders">
          <div className="profile-orders-list">
            {items.map((item) => (
              <article className="profile-order-item" key={item.id}>
                <div className="profile-order-top">
                  <span className="profile-order-id">{item.title}</span>
                  <span className="profile-order-date">{new Date(item.created_at).toLocaleString()}</span>
                </div>
                <div className="profile-order-meta">
                  <span>{item.body || "-"}</span>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
