import axios from "axios";
import { getTelegramInitData, getTelegramUserId, waitForTelegramInitData, waitForTelegramUserId } from "./telegram";

export const browserApi = axios.create({
  baseURL: "/api/backend",
  timeout: 10000,
  validateStatus: () => true,
});

browserApi.interceptors.request.use(async (config) => {
  let telegramInitData = getTelegramInitData();
  if (!telegramInitData) {
    telegramInitData = await waitForTelegramInitData();
  }

  let telegramUserId = getTelegramUserId();
  if (!telegramUserId) {
    telegramUserId = await waitForTelegramUserId();
  }

  const headers = config.headers ?? {};
  if (telegramUserId) {
    (headers as Record<string, string>)["X-Telegram-User-Id"] = String(telegramUserId);
  }
  if (telegramInitData) {
    (headers as Record<string, string>)["X-Telegram-Init-Data"] = telegramInitData;
  }
  config.headers = headers;
  return config;
});
