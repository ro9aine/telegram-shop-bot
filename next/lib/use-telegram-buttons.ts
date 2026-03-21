"use client";

import { useEffect } from "react";

type MainButtonOptions = {
  text: string;
  enabled: boolean;
  loading?: boolean;
  visible?: boolean;
  onClick: () => void;
};

export function useTelegramBackButton(onClick: () => void, visible = true): void {
  useEffect(() => {
    const webApp = window.Telegram?.WebApp;
    const backButton = webApp?.BackButton;
    if (!webApp || !backButton) {
      return;
    }

    const handler = () => onClick();
    if (visible) {
      backButton.show();
      webApp.onEvent?.("backButtonClicked", handler);
    } else {
      backButton.hide();
    }

    return () => {
      webApp.offEvent?.("backButtonClicked", handler);
      backButton.hide();
    };
  }, [onClick, visible]);
}

export function useTelegramMainButton(options: MainButtonOptions): void {
  const { text, enabled, loading = false, visible = true, onClick } = options;

  useEffect(() => {
    const webApp = window.Telegram?.WebApp;
    const mainButton = webApp?.MainButton;
    if (!webApp || !mainButton) {
      return;
    }

    const handler = () => onClick();
    webApp.onEvent?.("mainButtonClicked", handler);
    return () => webApp.offEvent?.("mainButtonClicked", handler);
  }, [onClick]);

  useEffect(() => {
    const mainButton = window.Telegram?.WebApp?.MainButton;
    if (!mainButton) {
      return;
    }

    if (!visible) {
      mainButton.hide();
      return;
    }

    mainButton.setText(text);
    if (loading) {
      mainButton.showProgress(true);
    } else {
      mainButton.hideProgress();
    }

    if (enabled) {
      mainButton.enable();
    } else {
      mainButton.disable();
    }
    mainButton.show();

    return () => {
      mainButton.hideProgress();
      mainButton.hide();
    };
  }, [enabled, loading, text, visible]);
}
