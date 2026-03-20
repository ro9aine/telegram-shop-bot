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
