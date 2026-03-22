"""
URL configuration for shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from botconfig.views import (
    basket_add_item_view,
    basket_clear_view,
    basket_item_view,
    basket_view,
    catalog_categories_view,
    catalog_product_detail_view,
    catalog_products_view,
    checkout_order_view,
    internal_active_orders_view,
    internal_basket_add_item_view,
    internal_basket_clear_view,
    internal_basket_item_view,
    internal_basket_view,
    internal_bot_settings_view,
    internal_broadcast_complete_view,
    internal_broadcast_next_view,
    internal_checkout_order_view,
    internal_faq_search_view,
    internal_order_mark_paid_view,
    internal_order_status_view,
    notifications_list_view,
    notifications_mark_read_view,
    order_mark_paid_view,
    orders_list_view,
    profile_me_view,
    register_profile_view,
    required_channels_view,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path('internal/required-channels/', required_channels_view),
    path('internal/register-profile/', register_profile_view),
    path("internal/bot-settings/", internal_bot_settings_view),
    path("internal/orders/active/", internal_active_orders_view),
    path("internal/orders/<int:order_id>/status/", internal_order_status_view),
    path("internal/orders/<int:order_id>/mark-paid/", internal_order_mark_paid_view),
    path("internal/faq/search/", internal_faq_search_view),
    path("internal/broadcasts/next/", internal_broadcast_next_view),
    path("internal/broadcasts/<int:broadcast_id>/complete/", internal_broadcast_complete_view),
    path("internal/basket/<int:telegram_user_id>/", internal_basket_view),
    path("internal/basket/<int:telegram_user_id>/items/", internal_basket_add_item_view),
    path("internal/basket/<int:telegram_user_id>/items/<int:product_id>/", internal_basket_item_view),
    path("internal/basket/<int:telegram_user_id>/clear/", internal_basket_clear_view),
    path("internal/orders/checkout/<int:telegram_user_id>/", internal_checkout_order_view),
    path("api/catalog/categories/", catalog_categories_view),
    path("api/catalog/products/", catalog_products_view),
    path("api/catalog/products/<int:product_id>/", catalog_product_detail_view),
    path("api/basket/", basket_view),
    path("api/basket/items/", basket_add_item_view),
    path("api/basket/items/<int:product_id>/", basket_item_view),
    path("api/basket/clear/", basket_clear_view),
    path("api/orders/checkout/", checkout_order_view),
    path("api/orders/<int:order_id>/mark-paid/", order_mark_paid_view),
    path("api/orders/", orders_list_view),
    path("api/notifications/", notifications_list_view),
    path("api/notifications/mark-read/", notifications_mark_read_view),
    path("api/profile/me/", profile_me_view),
]
