"use client";

import { useEffect, useState } from "react";

import { getTelegramWebAppUser, type TelegramWebAppUser } from "./telegram";

const POLL_INTERVAL_MS = 200;
const MAX_POLL_ATTEMPTS = 20;

export function useTelegramWebAppUser(): TelegramWebAppUser | null {
  const [user, setUser] = useState<TelegramWebAppUser | null>(null);

  useEffect(() => {
    let attempts = 0;

    const syncUser = (): boolean => {
      const nextUser = getTelegramWebAppUser();
      if (!nextUser) {
        return false;
      }
      setUser(nextUser);
      return true;
    };

    if (syncUser()) {
      return;
    }

    const intervalId = window.setInterval(() => {
      attempts += 1;
      if (syncUser() || attempts >= MAX_POLL_ATTEMPTS) {
        window.clearInterval(intervalId);
      }
    }, POLL_INTERVAL_MS);

    return () => window.clearInterval(intervalId);
  }, []);

  return user;
}
