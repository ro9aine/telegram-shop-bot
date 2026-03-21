import json
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import ProgrammingError, transaction
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .models import BasketItem, Category, Order, OrderItem, Product, RequiredChannel, Subcategory, TelegramProfile


def _is_internal_request(request: HttpRequest) -> bool:
    remote_addr = request.META.get("REMOTE_ADDR")
    supplied_token = request.headers.get("X-Internal-Token", "")
    expected_token = getattr(settings, "INTERNAL_API_TOKEN", "")

    if expected_token:
        return supplied_token == expected_token

    return remote_addr in {"127.0.0.1", "::1"}


def required_channels_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden:
    if not _is_internal_request(request):
        return HttpResponseForbidden("Local access only")

    channels = list(
        RequiredChannel.objects.filter(is_active=True)
        .order_by("title")
        .values("title", "chat_id", "invite_link")
    )
    return JsonResponse({"channels": channels})


def _category_payload(category: Category) -> dict[str, int | str | None]:
    return {
        "id": category.id,
        "title": category.title,
        "parent_id": None,
    }


def _subcategory_payload(subcategory: Subcategory) -> dict[str, int | str]:
    return {
        "id": -subcategory.id,
        "title": subcategory.title,
        "parent_id": subcategory.category_id,
    }


def _product_payload(product: Product) -> dict[str, int | str | list[str]]:
    catalog_id = -product.subcategory_id if product.subcategory_id else product.category_id
    return {
        "id": product.id,
        "category_id": catalog_id,
        "title": product.title,
        "description": product.description,
        "price": str(product.price),
        "images": [image.image_url for image in product.images.all()],
    }


def _resolve_profile(request: HttpRequest) -> TelegramProfile | None:
    raw = request.headers.get("X-Telegram-User-Id", "").strip()
    if not raw:
        return None
    try:
        user_id = int(raw)
    except ValueError:
        return None
    return TelegramProfile.objects.filter(telegram_user_id=user_id).first()


def _basket_item_payload(item: BasketItem) -> dict[str, int | str | None]:
    image = item.product.images.first()
    return {
        "product_id": item.product_id,
        "title": item.product.title,
        "price": str(item.product.price),
        "image": image.image_url if image else None,
        "quantity": item.quantity,
    }


def _basket_payload(profile: TelegramProfile) -> dict[str, object]:
    items = list(
        BasketItem.objects.filter(profile=profile)
        .select_related("product")
        .prefetch_related("product__images")
    )
    return {"items": [_basket_item_payload(item) for item in items]}


def _profile_payload(profile: TelegramProfile) -> dict[str, int | str]:
    return {
        "telegram_user_id": profile.telegram_user_id,
        "username": profile.username,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "photo_url": profile.photo_url,
        "phone_number": profile.phone_number,
    }


def _basket_total(items: list[BasketItem]) -> Decimal:
    total = Decimal("0")
    for item in items:
        total += item.product.price * item.quantity
    return total


@require_GET
def catalog_categories_view(request: HttpRequest) -> JsonResponse:
    categories = list(Category.objects.filter(is_active=True).order_by("title"))
    category_ids = [category.id for category in categories]
    try:
        subcategories = list(
            Subcategory.objects.filter(is_active=True, category_id__in=category_ids)
            .select_related("category")
            .order_by("title")
        )
    except ProgrammingError:
        # Temporary compatibility for DBs where migrations are not applied yet.
        subcategories = []
    payload = [_category_payload(category) for category in categories]
    payload.extend(_subcategory_payload(subcategory) for subcategory in subcategories)
    return JsonResponse({"categories": payload})


@require_GET
def catalog_products_view(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
    category_raw = request.GET.get("category_id")
    page_raw = request.GET.get("page", "1")
    page_size_raw = request.GET.get("page_size", "5")

    try:
        page = max(1, int(page_raw))
        page_size = max(1, min(50, int(page_size_raw)))
    except ValueError:
        return HttpResponseBadRequest("Invalid paging values")

    products = Product.objects.filter(is_active=True).prefetch_related("images").order_by("id")
    if category_raw:
        try:
            category_id = int(category_raw)
        except ValueError:
            return HttpResponseBadRequest("Invalid category_id")
        try:
            if category_id < 0:
                products = products.filter(subcategory_id=abs(category_id))
            else:
                products = products.filter(category_id=category_id, subcategory__isnull=True)
        except ProgrammingError:
            products = products.filter(category_id=abs(category_id))

    total = products.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages)
    offset = (page - 1) * page_size
    items = products[offset : offset + page_size]

    return JsonResponse(
        {
            "items": [_product_payload(product) for product in items],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": total_pages,
            },
        }
    )


@require_GET
def catalog_product_detail_view(request: HttpRequest, product_id: int) -> JsonResponse | HttpResponseNotFound:
    product = Product.objects.filter(id=product_id, is_active=True).prefetch_related("images").first()
    if product is None:
        return HttpResponseNotFound("Product not found")

    return JsonResponse({"item": _product_payload(product)})


@require_GET
def basket_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden:
    profile = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden("Telegram profile not found. Register in bot first.")
    return JsonResponse(_basket_payload(profile))


@csrf_exempt
@require_http_methods(["POST"])
def basket_add_item_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden | HttpResponseBadRequest:
    profile = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden("Telegram profile not found. Register in bot first.")

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        product_id = int(payload["product_id"])
        quantity = max(1, int(payload.get("quantity", 1)))
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        return HttpResponseBadRequest("Invalid payload")

    product = Product.objects.filter(id=product_id, is_active=True).first()
    if product is None:
        return HttpResponseBadRequest("Product not found")

    item, created = BasketItem.objects.get_or_create(profile=profile, product=product, defaults={"quantity": quantity})
    if not created:
        item.quantity += quantity
        item.save(update_fields=["quantity", "updated_at"])

    return JsonResponse(_basket_payload(profile))


@csrf_exempt
@require_http_methods(["PATCH", "DELETE"])
def basket_item_view(
    request: HttpRequest,
    product_id: int,
) -> JsonResponse | HttpResponseForbidden | HttpResponseBadRequest:
    profile = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden("Telegram profile not found. Register in bot first.")

    item = BasketItem.objects.filter(profile=profile, product_id=product_id).first()
    if request.method == "DELETE":
        if item:
            item.delete()
        return JsonResponse(_basket_payload(profile))

    if item is None:
        return HttpResponseBadRequest("Basket item not found")

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        quantity = int(payload["quantity"])
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        return HttpResponseBadRequest("Invalid payload")

    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])

    return JsonResponse(_basket_payload(profile))


@csrf_exempt
@require_http_methods(["POST"])
def basket_clear_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden:
    profile = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden("Telegram profile not found. Register in bot first.")
    BasketItem.objects.filter(profile=profile).delete()
    return JsonResponse({"items": []})


@csrf_exempt
@require_http_methods(["POST"])
def checkout_order_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden | HttpResponseBadRequest:
    profile = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden("Telegram profile not found. Register in bot first.")

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid payload")

    recipient_name = str(payload.get("recipient_name") or "").strip()
    phone_number = str(payload.get("phone_number") or "").strip()
    delivery_address = str(payload.get("delivery_address") or "").strip()
    delivery_comment = str(payload.get("delivery_comment") or "").strip()

    if not recipient_name:
        return HttpResponseBadRequest("recipient_name is required")
    if not phone_number:
        return HttpResponseBadRequest("phone_number is required")
    if not delivery_address:
        return HttpResponseBadRequest("delivery_address is required")

    basket_items = list(
        BasketItem.objects.filter(profile=profile)
        .select_related("product")
        .prefetch_related("product__images")
    )
    if not basket_items:
        return HttpResponseBadRequest("Basket is empty")

    try:
        total_amount = _basket_total(basket_items)
    except InvalidOperation:
        return HttpResponseBadRequest("Unable to calculate basket total")

    with transaction.atomic():
        order = Order.objects.create(
            profile=profile,
            recipient_name=recipient_name,
            phone_number=phone_number,
            delivery_address=delivery_address,
            delivery_comment=delivery_comment,
            total_amount=total_amount,
        )

        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    product=item.product,
                    title=item.product.title,
                    price=item.product.price,
                    quantity=item.quantity,
                )
                for item in basket_items
            ]
        )

        BasketItem.objects.filter(profile=profile).delete()

    return JsonResponse(
        {
            "order": {
                "id": order.id,
                "status": order.status,
                "total_amount": str(order.total_amount),
                "items_count": len(basket_items),
            }
        }
    )


@require_GET
def profile_me_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden:
    profile = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden("Telegram profile not found. Register in bot first.")
    return JsonResponse({"profile": _profile_payload(profile)})


@csrf_exempt
def register_profile_view(
    request: HttpRequest,
) -> JsonResponse | HttpResponseForbidden | HttpResponseBadRequest:
    if not _is_internal_request(request):
        return HttpResponseForbidden("Local access only")

    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    try:
        payload = json.loads(request.body.decode("utf-8"))
        telegram_user_id = int(payload["telegram_user_id"])
        phone_number = str(payload["phone_number"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return HttpResponseBadRequest("Invalid payload")

    profile, _ = TelegramProfile.objects.update_or_create(
        telegram_user_id=telegram_user_id,
        defaults={
            "username": str(payload.get("username") or ""),
            "first_name": str(payload.get("first_name") or ""),
            "last_name": str(payload.get("last_name") or ""),
            "photo_url": str(payload.get("photo_url") or ""),
            "phone_number": phone_number,
        },
    )
    return JsonResponse({"id": profile.id, "telegram_user_id": profile.telegram_user_id})
