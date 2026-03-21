import { browserApi } from "./http";

export type BasketItem = {
  productId: number;
  title: string;
  price: string;
  image: string | null;
  quantity: number;
};

type BasketPayload = {
  items?: Array<{
    product_id: number;
    title: string;
    price: string;
    image: string | null;
    quantity: number;
  }>;
};

type CheckoutPayload = {
  recipient_name: string;
  phone_number: string;
  delivery_address: string;
  delivery_comment: string;
};

type CheckoutResponse = {
  order?: {
    id: number;
    status: string;
    total_amount: string;
    items_count: number;
  };
};

function normalizePayload(payload: BasketPayload | null | undefined): BasketItem[] {
  if (!payload?.items || !Array.isArray(payload.items)) {
    return [];
  }
  return payload.items
    .map((item) => ({
      productId: Number(item.product_id),
      title: String(item.title ?? ""),
      price: String(item.price ?? "0"),
      image: item.image ? String(item.image) : null,
      quantity: Math.max(1, Number(item.quantity) || 1),
    }))
    .filter((item) => Number.isFinite(item.productId) && item.productId > 0 && item.title.length > 0);
}

function publish(items: BasketItem[]): BasketItem[] {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("basket:changed", { detail: items }));
  }
  return items;
}

export async function fetchBasket(): Promise<BasketItem[]> {
  const response = await browserApi.get<BasketPayload>("/basket/");
  if (response.status < 200 || response.status >= 300) {
    return [];
  }
  return normalizePayload(response.data);
}

export async function addToBasket(
  item: Omit<BasketItem, "quantity">,
  quantity = 1,
): Promise<BasketItem[]> {
  const response = await browserApi.post<BasketPayload>("/basket/items/", {
    product_id: item.productId,
    quantity: Math.max(1, quantity),
  });
  if (response.status < 200 || response.status >= 300) {
    return [];
  }
  return publish(normalizePayload(response.data));
}

export async function updateBasketQuantity(productId: number, quantity: number): Promise<BasketItem[]> {
  const response = await browserApi.patch<BasketPayload>(`/basket/items/${productId}/`, {
    quantity: Math.max(0, Math.floor(quantity)),
  });
  if (response.status < 200 || response.status >= 300) {
    return [];
  }
  return publish(normalizePayload(response.data));
}

export async function removeFromBasket(productId: number): Promise<BasketItem[]> {
  const response = await browserApi.delete<BasketPayload>(`/basket/items/${productId}/`);
  if (response.status < 200 || response.status >= 300) {
    return [];
  }
  return publish(normalizePayload(response.data));
}

export async function clearBasket(): Promise<BasketItem[]> {
  const response = await browserApi.post<BasketPayload>("/basket/clear/");
  if (response.status < 200 || response.status >= 300) {
    return [];
  }
  return publish(normalizePayload(response.data));
}

export async function checkoutBasket(payload: CheckoutPayload): Promise<CheckoutResponse["order"] | null> {
  const response = await browserApi.post<CheckoutResponse>("/orders/checkout/", payload);
  if (response.status < 200 || response.status >= 300) {
    return null;
  }
  const order = response.data.order;
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("basket:changed", { detail: [] }));
  }
  return order ?? null;
}

export function basketTotal(items: BasketItem[]): number {
  return items.reduce((sum, item) => {
    const price = Number.parseFloat(item.price.replace(",", "."));
    if (!Number.isFinite(price)) {
      return sum;
    }
    return sum + price * item.quantity;
  }, 0);
}
