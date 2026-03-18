import json

from django.conf import settings
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import RequiredChannel, TelegramProfile


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
