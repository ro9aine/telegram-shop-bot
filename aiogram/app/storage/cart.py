from collections import defaultdict

_CARTS: dict[int, dict[int, int]] = defaultdict(dict)


def add_to_cart(user_id: int, product_id: int, quantity: int = 1) -> int:
    cart = _CARTS[user_id]
    cart[product_id] = cart.get(product_id, 0) + max(1, quantity)
    return cart[product_id]
