"""
URL configuration for Store_shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
# my_store_project/urls.py

from django.contrib import admin
from django.urls import path, include # Make sure include is imported
from django.conf import settings # For media files
from django.conf.urls.static import static # For media files
# We need to import the dashboard view directly if it's the homepage
from shop import views as shop_views # Import views from your shop app

urlpatterns = [
    path('admin/', admin.site.urls),

    # Set the dashboard as the homepage
    path('', shop_views.dashboard_view, name='home_dashboard'),
    # If you prefer the product list as the homepage, use this instead:
    # path('', shop_views.product_list, name='home_product_list'),


    # Include the URLs from your shop app under the '/shop/' prefix
    # This keeps other shop-specific URLs like /shop/cart/, /shop/profile/ organized.
    path('shop/', include('shop.urls', namespace='shop')),

    # Note: The previous RedirectView for the root URL has been replaced by the direct view path above.
]

# Add this for serving media files (e.g., product images) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Add this for serving static files during development if not handled by webserver in production
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
