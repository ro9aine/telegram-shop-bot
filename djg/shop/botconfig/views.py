import json
from decimal import Decimal, InvalidOperation
from django.utils import timezone

from django.conf import settings
from django.db import ProgrammingError, transaction
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .telegram_auth import validate_telegram_init_data
from .models import (
    BasketItem,
    BotSettings,
    Broadcast,
    Category,
    FAQ,
    Order,
    OrderItem,
    Product,
    RequiredChannel,
    Subcategory,
    TelegramProfile,
    UserNotification,
)


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


def _resolve_profile(request: HttpRequest) -> tuple[TelegramProfile | None, str | None]:
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    auth = validate_telegram_init_data(
        init_data=init_data,
        bot_token=getattr(settings, "TELEGRAM_BOT_TOKEN", ""),
        max_age_seconds=getattr(settings, "TELEGRAM_INIT_DATA_MAX_AGE_SECONDS", 86400),
    )
    if auth is None:
        return None, "Invalid Telegram init data."

    raw = request.headers.get("X-Telegram-User-Id", "").strip()
    if raw:
        try:
            header_user_id = int(raw)
        except ValueError:
            return None, "Invalid Telegram user id."
        if header_user_id != auth.user_id:
            return None, "Telegram user mismatch."

    profile = TelegramProfile.objects.filter(telegram_user_id=auth.user_id).first()
    if profile is None:
        return None, "Telegram profile not found. Register in bot first."
    return profile, None


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
        .order_by("id")
    )
    return {"items": [_basket_item_payload(item) for item in items]}


def _resolve_internal_profile(telegram_user_id: int) -> TelegramProfile:
    profile, _ = TelegramProfile.objects.get_or_create(
        telegram_user_id=telegram_user_id,
        defaults={
            "phone_number": "",
            "username": "",
            "first_name": "",
            "last_name": "",
            "photo_url": "",
        },
    )
    return profile


def _profile_payload(profile: TelegramProfile) -> dict[str, int | str]:
    return {
        "telegram_user_id": profile.telegram_user_id,
        "username": profile.username,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "photo_url": profile.photo_url,
        "phone_number": profile.phone_number,
    }


def _order_payload(order: Order, items_count: int) -> dict[str, int | str]:
    return {
        "id": order.id,
        "status": order.status,
        "payment_status": order.payment_status,
        "total_amount": str(order.total_amount),
        "items_count": items_count,
    }


def _notification_payload(notification: UserNotification) -> dict[str, int | str | bool | None]:
    return {
        "id": notification.id,
        "title": notification.title,
        "body": notification.body,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat(),
        "read_at": notification.read_at.isoformat() if notification.read_at else None,
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
    profile, error = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden(error or "Forbidden")
    return JsonResponse(_basket_payload(profile))


@require_GET
def internal_basket_view(request: HttpRequest, telegram_user_id: int) -> JsonResponse | HttpResponseForbidden:
    if not _is_internal_request(request):
        return HttpResponseForbidden("Local access only")
    profile = _resolve_internal_profile(telegram_user_id)
    return JsonResponse(_basket_payload(profile))


@csrf_exempt
@require_http_methods(["POST"])
def basket_add_item_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden | HttpResponseBadRequest:
    profile, error = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden(error or "Forbidden")

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
@require_http_methods(["POST"])
def internal_basket_add_item_view(
    request: HttpRequest,
    telegram_user_id: int,
) -> JsonResponse | HttpResponseForbidden | HttpResponseBadRequest:
    if not _is_internal_request(request):
        return HttpResponseForbidden("Local access only")
    profile = _resolve_internal_profile(telegram_user_id)

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
    profile, error = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden(error or "Forbidden")

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
@require_http_methods(["PATCH", "DELETE"])
def internal_basket_item_view(
    request: HttpRequest,
    telegram_user_id: int,
    product_id: int,
) -> JsonResponse | HttpResponseForbidden | HttpResponseBadRequest:
    if not _is_internal_request(request):
        return HttpResponseForbidden("Local access only")
    profile = _resolve_internal_profile(telegram_user_id)

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
    profile, error = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden(error or "Forbidden")
    BasketItem.objects.filter(profile=profile).delete()
    return JsonResponse({"items": []})


@csrf_exempt
@require_http_methods(["POST"])
def internal_basket_clear_view(
    request: HttpRequest,
    telegram_user_id: int,
) -> JsonResponse | HttpResponseForbidden:
    if not _is_internal_request(request):
        return HttpResponseForbidden("Local access only")
    profile = _resolve_internal_profile(telegram_user_id)
    BasketItem.objects.filter(profile=profile).delete()
    return JsonResponse({"items": []})


@csrf_exempt
@require_http_methods(["POST"])
def checkout_order_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden | HttpResponseBadRequest:
    profile, error = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden(error or "Forbidden")

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
            "order": _order_payload(order, len(basket_items))
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def internal_checkout_order_view(
    request: HttpRequest,
    telegram_user_id: int,
) -> JsonResponse | HttpResponseForbidden | HttpResponseBadRequest:
    if not _is_internal_request(request):
        return HttpResponseForbidden("Local access only")
    profile = _resolve_internal_profile(telegram_user_id)

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid payload")

    recipient_name = str(payload.get("recipient_name") or "").strip()
    phone_number = str(payload.get("phone_number") or "").strip() or profile.phone_number
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

    return JsonResponse({"order": _order_payload(order, len(basket_items))})


@csrf_exempt
@require_http_methods(["POST"])
def order_mark_paid_view(
    request: HttpRequest,
    order_id: int,
) -> JsonResponse | HttpResponseForbidden | HttpResponseNotFound:
    profile, error = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden(error or "Forbidden")

    order = Order.objects.filter(id=order_id, profile=profile).first()
    if order is None:
        return HttpResponseNotFound("Order not found")

    if order.payment_status != Order.PAYMENT_PAID:
        order.payment_status = Order.PAYMENT_PAID
        order.save(update_fields=["payment_status", "updated_at"])

    items_count = order.items.count()
    return JsonResponse({"order": _order_payload(order, items_count)})


@csrf_exempt
@require_http_methods(["POST"])
def internal_order_mark_paid_view(
    request: HttpRequest,
    order_id: int,
) -> JsonResponse | HttpResponseForbidden | HttpResponseNotFound:
    if not _is_internal_request(request):
        return HttpResponseForbidden("Local access only")
    order = Order.objects.prefetch_related("items").filter(id=order_id).first()
    if order is None:
        return HttpResponseNotFound("Order not found")
    if order.payment_status != Order.PAYMENT_PAID:
        order.payment_status = Order.PAYMENT_PAID
        order.save(update_fields=["payment_status", "updated_at"])
    return JsonResponse({"order": _order_payload(order, order.items.count())})


@require_GET
def profile_me_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden:
    profile, error = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden(error or "Forbidden")
    return JsonResponse({"profile": _profile_payload(profile)})


@require_GET
def orders_list_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden:
    profile, error = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden(error or "Forbidden")

    orders = (
        Order.objects.filter(profile=profile)
        .prefetch_related("items")
        .order_by("-created_at", "-id")
    )

    payload = [
        {
            **_order_payload(order, order.items.count()),
            "created_at": order.created_at.isoformat(),
        }
        for order in orders
    ]
    return JsonResponse({"orders": payload})


@require_GET
def notifications_list_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden:
    profile, error = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden(error or "Forbidden")

    unread_only = str(request.GET.get("unread_only") or "").lower() in {"1", "true", "yes"}
    items = UserNotification.objects.filter(profile=profile)
    if unread_only:
        items = items.filter(is_read=False)

    payload = [_notification_payload(item) for item in items[:100]]
    unread_count = UserNotification.objects.filter(profile=profile, is_read=False).count()
    return JsonResponse({"items": payload, "unread_count": unread_count})


@csrf_exempt
@require_http_methods(["POST"])
def notifications_mark_read_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden:
    profile, error = _resolve_profile(request)
    if profile is None:
        return HttpResponseForbidden(error or "Forbidden")

    now = timezone.now()
    UserNotification.objects.filter(profile=profile, is_read=False).update(is_read=True, read_at=now)
    return JsonResponse({"ok": True})


def _order_details_payload(order: Order) -> dict[str, object]:
    return {
        "id": order.id,
        "telegram_user_id": order.profile.telegram_user_id,
        "recipient_name": order.recipient_name,
        "phone_number": order.phone_number,
        "delivery_address": order.delivery_address,
        "delivery_comment": order.delivery_comment,
        "status": order.status,
        "payment_status": order.payment_status,
        "total_amount": str(order.total_amount),
        "items": [
            {
                "product_id": item.product_id,
                "title": item.title,
                "price": str(item.price),
                "quantity": item.quantity,
            }
            for item in order.items.all()
        ],
    }


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


@require_GET
def internal_bot_settings_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden:
    if not _is_internal_request(request):
        return HttpResponseForbidden("Local access only")

    settings_obj = BotSettings.objects.first()
    return JsonResponse(
        {
            "admin_chat_id": settings_obj.admin_chat_id if settings_obj else None,
            "admin_telegram_ids": settings_obj.admin_telegram_ids if settings_obj else "",
        }
    )


@require_GET
def internal_active_orders_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden:
    if not _is_internal_request(request):
        return HttpResponseForbidden("Local access only")

    orders = (
        Order.objects.exclude(status=Order.STATUS_DONE)
        .select_related("profile")
        .prefetch_related("items")
        .order_by("-created_at", "-id")
    )
    return JsonResponse({"orders": [_order_details_payload(order) for order in orders]})


@csrf_exempt
@require_http_methods(["POST"])
def internal_order_status_view(
    request: HttpRequest,
    order_id: int,
) -> JsonResponse | HttpResponseForbidden | HttpResponseNotFound | HttpResponseBadRequest:
    if not _is_internal_request(request):
        return HttpResponseForbidden("Local access only")

    order = Order.objects.select_related("profile").prefetch_related("items").filter(id=order_id).first()
    if order is None:
        return HttpResponseNotFound("Order not found")

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid payload")

    status = str(payload.get("status") or "").strip()
    if status not in {choice[0] for choice in Order.STATUS_CHOICES}:
        return HttpResponseBadRequest("Invalid status")

    if order.status != status:
        order.status = status
        order.save(update_fields=["status", "updated_at"])

    return JsonResponse({"order": _order_details_payload(order)})


@require_GET
def internal_faq_search_view(request: HttpRequest) -> JsonResponse | HttpResponseForbidden:
    if not _is_internal_request(request):
        return HttpResponseForbidden("Local access only")

    query = str(request.GET.get("q") or "").strip()
    limit_raw = str(request.GET.get("limit") or "10")
    try:
        limit = max(1, min(20, int(limit_raw)))
    except ValueError:
        limit = 10

    qs = FAQ.objects.filter(is_active=True)
    if query:
        qs = qs.filter(question__icontains=query)
        qs = qs.order_by("question")
    else:
        qs = qs.order_by("-is_popular", "question")

    items = list(qs[:limit])
    return JsonResponse(
        {
            "items": [
                {
                    "id": item.id,
                    "question": item.question,
                    "answer": item.answer,
                }
                for item in items
            ]
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def internal_broadcast_next_view(
    request: HttpRequest,
) -> JsonResponse | HttpResponseForbidden:
    if not _is_internal_request(request):
        return HttpResponseForbidden("Local access only")

    broadcast = Broadcast.objects.filter(status=Broadcast.STATUS_READY).order_by("created_at", "id").first()
    if broadcast is None:
        return JsonResponse({"broadcast": None})

    recipients = list(TelegramProfile.objects.values_list("telegram_user_id", flat=True))
    return JsonResponse(
        {
            "broadcast": {
                "id": broadcast.id,
                "text": broadcast.text,
                "image_url": broadcast.image_url,
                "recipients": recipients,
            }
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def internal_broadcast_complete_view(
    request: HttpRequest,
    broadcast_id: int,
) -> JsonResponse | HttpResponseForbidden | HttpResponseNotFound | HttpResponseBadRequest:
    if not _is_internal_request(request):
        return HttpResponseForbidden("Local access only")

    broadcast = Broadcast.objects.filter(id=broadcast_id).first()
    if broadcast is None:
        return HttpResponseNotFound("Broadcast not found")

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        delivered_count = max(0, int(payload.get("delivered_count", 0)))
        failed_count = max(0, int(payload.get("failed_count", 0)))
    except (ValueError, TypeError, json.JSONDecodeError):
        return HttpResponseBadRequest("Invalid payload")

    broadcast.delivered_count = delivered_count
    broadcast.failed_count = failed_count
    broadcast.status = Broadcast.STATUS_SENT
    broadcast.sent_at = timezone.now()
    broadcast.save(update_fields=["delivered_count", "failed_count", "status", "sent_at", "updated_at"])
    return JsonResponse({"ok": True})
