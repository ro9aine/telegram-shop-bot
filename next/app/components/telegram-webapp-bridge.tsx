"use client";

import { useEffect } from "react";

function applyThemeParams(): void {
  const webApp = window.Telegram?.WebApp;
  const root = document.documentElement;
  if (!webApp || !root) {
    return;
  }

  const theme = webApp.themeParams || {};
  const bg = theme.bg_color || "";
  const paper = theme.secondary_bg_color || "";
  const text = theme.text_color || "";
  const muted = theme.hint_color || "";
  const accent = theme.button_color || "";

  if (bg) {
    root.style.setProperty("--tg-bg-color", bg);
    root.style.setProperty("--bg", bg);
  }
  if (paper) {
    root.style.setProperty("--tg-secondary-bg-color", paper);
    root.style.setProperty("--paper", paper);
  }
  if (text) {
    root.style.setProperty("--tg-text-color", text);
    root.style.setProperty("--text", text);
  }
  if (muted) {
    root.style.setProperty("--tg-hint-color", muted);
    root.style.setProperty("--muted", muted);
  }
  if (accent) {
    root.style.setProperty("--tg-button-color", accent);
    root.style.setProperty("--accent", accent);
  }

  root.style.colorScheme = webApp.colorScheme === "dark" ? "dark" : "light";
}

export default function TelegramWebAppBridge() {
  useEffect(() => {
    let detach: (() => void) | null = null;
    let attempts = 0;

    const bootstrap = (): boolean => {
      const webApp = window.Telegram?.WebApp;
      if (!webApp) {
        return false;
      }

      webApp.ready?.();
      webApp.expand?.();
      applyThemeParams();

      const onThemeChanged = () => applyThemeParams();
      webApp.onEvent?.("themeChanged", onThemeChanged);
      detach = () => webApp.offEvent?.("themeChanged", onThemeChanged);
      return true;
    };

    if (bootstrap()) {
      return () => detach?.();
    }

    const timer = window.setInterval(() => {
      attempts += 1;
      if (bootstrap() || attempts >= 50) {
        window.clearInterval(timer);
      }
    }, 100);

    return () => {
      window.clearInterval(timer);
      detach?.();
    };
  }, []);

  return null;
}
