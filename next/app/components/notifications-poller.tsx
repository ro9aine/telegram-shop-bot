"use client";

import { notification } from "antd";
import { useEffect, useRef } from "react";

import { fetchNotifications } from "../../lib/notifications";

const POLL_INTERVAL_MS = 15000;

export default function NotificationsPoller() {
  const shownIdsRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    let disposed = false;

    const poll = async () => {
      const { items } = await fetchNotifications(true);
      if (disposed || !items.length) {
        return;
      }

      for (const item of items) {
        if (shownIdsRef.current.has(item.id)) {
          continue;
        }
        shownIdsRef.current.add(item.id);
        notification.info({
          message: item.title,
          description: item.body || "You have a new notification",
          placement: "topRight",
          duration: 4,
        });
      }
    };

    void poll();
    const intervalId = window.setInterval(() => {
      void poll();
    }, POLL_INTERVAL_MS);

    return () => {
      disposed = true;
      window.clearInterval(intervalId);
    };
  }, []);

  return null;
}
