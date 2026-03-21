from aiogram.filters.callback_data import CallbackData


class CatalogCategoryCallback(CallbackData, prefix="cat"):
    category_id: int


class CatalogPageCallback(CallbackData, prefix="catp"):
    category_id: int
    page: int


class CatalogProductCallback(CallbackData, prefix="prd"):
    product_id: int
    category_id: int
    page: int


class CatalogBackCallback(CallbackData, prefix="catb"):
    parent_id: int


class CartAddCallback(CallbackData, prefix="crt"):
    product_id: int


class AdminOrderStatusCallback(CallbackData, prefix="admord"):
    order_id: int
    status: str


class CartChangeQtyCallback(CallbackData, prefix="crtu"):
    product_id: int
    delta: int


class CartRemoveCallback(CallbackData, prefix="crtr"):
    product_id: int


class CartClearCallback(CallbackData, prefix="crtc"):
    confirm: int


class CartCheckoutCallback(CallbackData, prefix="crto"):
    start: int


class OrderPaidCallback(CallbackData, prefix="ordp"):
    order_id: int


class CheckoutFlowCallback(CallbackData, prefix="ccfm"):
    action: str
