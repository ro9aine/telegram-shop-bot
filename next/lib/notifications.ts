import { browserApi } from "./http";

export type UserNotification = {
  id: number;
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
};

type NotificationsPayload = {
  items?: UserNotification[];
  unread_count?: number;
};

export async function fetchNotifications(unreadOnly = false): Promise<{
  items: UserNotification[];
  unreadCount: number;
}> {
  const response = await browserApi.get<NotificationsPayload>("/notifications/", {
    params: unreadOnly ? { unread_only: 1 } : undefined,
  });
  if (response.status < 200 || response.status >= 300) {
    return { items: [], unreadCount: 0 };
  }
  return {
    items: Array.isArray(response.data.items) ? response.data.items : [],
    unreadCount:
      typeof response.data.unread_count === "number" ? response.data.unread_count : 0,
  };
}

export async function markNotificationsRead(): Promise<boolean> {
  const response = await browserApi.post<{ ok?: boolean }>("/notifications/mark-read/");
  return response.status >= 200 && response.status < 300;
}
