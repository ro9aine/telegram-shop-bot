declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        onEvent?: (eventType: string, eventHandler: () => void) => void;
        offEvent?: (eventType: string, eventHandler: () => void) => void;
        ready?: () => void;
        expand?: () => void;
        openTelegramLink?: (url: string) => void;
        showAlert?: (message: string) => void;
        colorScheme?: "light" | "dark";
        themeParams?: {
          bg_color?: string;
          secondary_bg_color?: string;
          text_color?: string;
          hint_color?: string;
          button_color?: string;
          button_text_color?: string;
        };
        BackButton?: {
          show: () => void;
          hide: () => void;
        };
        MainButton?: {
          show: () => void;
          hide: () => void;
          enable: () => void;
          disable: () => void;
          setText: (text: string) => void;
          showProgress: (leaveActive?: boolean) => void;
          hideProgress: () => void;
        };
        initDataUnsafe?: {
          user?: {
            id?: number;
            username?: string;
            first_name?: string;
            last_name?: string;
            photo_url?: string;
          };
        };
        initData?: string;
      };
    };
  }
}

const TELEGRAM_USER_ID_CACHE_KEY = "shop:telegram_user_id";
const TELEGRAM_USER_CACHE_KEY = "shop:telegram_user";
const TELEGRAM_INIT_DATA_CACHE_KEY = "shop:telegram_init_data";

function fromSearchParams(): number | null {
  if (typeof window === "undefined") {
    return null;
  }
  const value = new URLSearchParams(window.location.search).get("tg_user_id");
  if (!value) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function fromTelegramWebApp(): number | null {
  if (typeof window === "undefined") {
    return null;
  }
  const id = window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
  return typeof id === "number" && Number.isFinite(id) ? id : null;
}

export type TelegramWebAppUser = {
  id: number;
  username: string;
  firstName: string;
  lastName: string;
  photoUrl: string;
};

function normalizeTelegramWebAppUser(user: {
  id?: number;
  username?: string;
  first_name?: string;
  last_name?: string;
  photo_url?: string;
}): TelegramWebAppUser | null {
  if (typeof user.id !== "number" || !Number.isFinite(user.id)) {
    return null;
  }

  return {
    id: user.id,
    username: user.username ?? "",
    firstName: user.first_name ?? "",
    lastName: user.last_name ?? "",
    photoUrl: user.photo_url ?? "",
  };
}

function cacheTelegramWebAppUser(user: TelegramWebAppUser): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(TELEGRAM_USER_ID_CACHE_KEY, String(user.id));
  window.localStorage.setItem(TELEGRAM_USER_CACHE_KEY, JSON.stringify(user));
}

function fromUserCache(): TelegramWebAppUser | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(TELEGRAM_USER_CACHE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as Partial<TelegramWebAppUser>;
    if (typeof parsed.id !== "number" || !Number.isFinite(parsed.id)) {
      return null;
    }

    return {
      id: parsed.id,
      username: typeof parsed.username === "string" ? parsed.username : "",
      firstName: typeof parsed.firstName === "string" ? parsed.firstName : "",
      lastName: typeof parsed.lastName === "string" ? parsed.lastName : "",
      photoUrl: typeof parsed.photoUrl === "string" ? parsed.photoUrl : "",
    };
  } catch {
    return null;
  }
}

export function getTelegramWebAppUser(): TelegramWebAppUser | null {
  if (typeof window === "undefined") {
    return null;
  }
  const user = window.Telegram?.WebApp?.initDataUnsafe?.user;
  if (user) {
    const normalized = normalizeTelegramWebAppUser(user);
    if (normalized) {
      cacheTelegramWebAppUser(normalized);
      return normalized;
    }
  }

  return fromUserCache();
}

function fromCache(): number | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = window.localStorage.getItem(TELEGRAM_USER_ID_CACHE_KEY);
  if (!raw) {
    return null;
  }
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : null;
}

export function getTelegramUserId(): number | null {
  if (typeof window === "undefined") {
    return null;
  }

  const webAppUser = getTelegramWebAppUser();
  if (webAppUser) {
    window.localStorage.setItem(TELEGRAM_USER_ID_CACHE_KEY, String(webAppUser.id));
    return webAppUser.id;
  }

  const fromQuery = fromSearchParams();
  if (fromQuery) {
    window.localStorage.setItem(TELEGRAM_USER_ID_CACHE_KEY, String(fromQuery));
    return fromQuery;
  }

  return fromCache();
}

function fromInitDataCache(): string {
  if (typeof window === "undefined") {
    return "";
  }
  return window.localStorage.getItem(TELEGRAM_INIT_DATA_CACHE_KEY) || "";
}

export function getTelegramInitData(): string {
  if (typeof window === "undefined") {
    return "";
  }
  const initData = (window.Telegram?.WebApp?.initData || "").trim();
  if (initData) {
    window.localStorage.setItem(TELEGRAM_INIT_DATA_CACHE_KEY, initData);
    return initData;
  }
  return fromInitDataCache();
}

export async function waitForTelegramInitData(
  attempts = 8,
  intervalMs = 120,
): Promise<string> {
  const immediate = getTelegramInitData();
  if (immediate) {
    return immediate;
  }
  if (typeof window === "undefined") {
    return "";
  }

  return new Promise((resolve) => {
    let tries = 0;
    const timer = window.setInterval(() => {
      tries += 1;
      const value = getTelegramInitData();
      if (value || tries >= attempts) {
        window.clearInterval(timer);
        resolve(value || "");
      }
    }, intervalMs);
  });
}

export async function waitForTelegramUserId(
  attempts = 8,
  intervalMs = 120,
): Promise<number | null> {
  const immediate = getTelegramUserId();
  if (immediate) {
    return immediate;
  }
  if (typeof window === "undefined") {
    return null;
  }

  return new Promise((resolve) => {
    let tries = 0;
    const timer = window.setInterval(() => {
      tries += 1;
      const value = getTelegramUserId();
      if (value || tries >= attempts) {
        window.clearInterval(timer);
        resolve(value ?? null);
      }
    }, intervalMs);
  });
}
