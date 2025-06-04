# shop/urls.py

from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

app_name = 'shop'

urlpatterns = [
    # Dashboard (General User)
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Product Catalog
    path('', views.product_list, name='product_list_all'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),

    # Cart Management
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item_quantity, name='update_cart_item_quantity'),

    # Checkout Process
    path('checkout/', views.checkout, name='checkout'),
    path('order_confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),

    # User/Customer Management
    path('register/', views.customer_register, name='customer_register'),
    path('profile/', views.customer_profile, name='customer_profile'),
    path('order_history/', views.order_history, name='order_history'),

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),

    # Password reset views
    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             success_url=reverse_lazy('shop:password_reset_done')
         ),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url=reverse_lazy('shop:password_reset_complete')
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # Seller Specific URLs
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/product/create/', views.create_product, name='seller_create_product'),
    path('seller/product/<int:product_id>/update/', views.update_product, name='seller_update_product'),
    path('seller/product/<int:product_id>/delete/', views.delete_product, name='seller_delete_product'),

    # Gemini AI Integration URL #  idea if i include ai bot to the shop
    path('seller/product/generate-description/', views.generate_product_description_ajax,
         name='generate_product_description_ajax'),

    # About Page URL
    path('about/', views.about_page_view, name='about_page'),
]
