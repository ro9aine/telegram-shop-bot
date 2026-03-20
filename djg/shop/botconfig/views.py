import json

from django.conf import settings
from django.db import ProgrammingError
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from .models import Category, Product, RequiredChannel, Subcategory, TelegramProfile


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
            "phone_number": phone_number,
        },
    )
    return JsonResponse({"id": profile.id, "telegram_user_id": profile.telegram_user_id})
