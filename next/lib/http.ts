import axios from "axios";
import { getTelegramUserId, waitForTelegramUserId } from "./telegram";

export const browserApi = axios.create({
  baseURL: "/api/backend",
  timeout: 10000,
  validateStatus: () => true,
});

browserApi.interceptors.request.use(async (config) => {
  let telegramUserId = getTelegramUserId();
  if (!telegramUserId) {
    telegramUserId = await waitForTelegramUserId();
  }
  if (!telegramUserId) {
    return config;
  }

  const headers = config.headers ?? {};
  (headers as Record<string, string>)["X-Telegram-User-Id"] = String(telegramUserId);
  config.headers = headers;
  return config;
});
