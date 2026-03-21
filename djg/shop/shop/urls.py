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
    profile_me_view,
    register_profile_view,
    required_channels_view,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path('internal/required-channels/', required_channels_view),
    path('internal/register-profile/', register_profile_view),
    path("api/catalog/categories/", catalog_categories_view),
    path("api/catalog/products/", catalog_products_view),
    path("api/catalog/products/<int:product_id>/", catalog_product_detail_view),
    path("api/basket/", basket_view),
    path("api/basket/items/", basket_add_item_view),
    path("api/basket/items/<int:product_id>/", basket_item_view),
    path("api/basket/clear/", basket_clear_view),
    path("api/orders/checkout/", checkout_order_view),
    path("api/profile/me/", profile_me_view),
]
