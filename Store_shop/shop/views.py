# shop/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction
from django.contrib import messages
from django.utils.text import slugify
import json

from .models import Category, Product, Order, OrderItem, Customer, ShippingAddress
from .forms import (
    CustomerRegistrationForm, ShippingAddressForm, UserUpdateForm,
    CustomerProfileUpdateForm, ProductForm
)


# --- Decorator for seller-only views ---
def seller_required(function):
    @login_required
    def wrap(request, *args, **kwargs):
        try:
            customer, created = Customer.objects.get_or_create(
                user=request.user,
                defaults={
                    'name': request.user.get_full_name() or request.user.username,
                    'email': request.user.email
                }
            )
            if customer.is_seller:
                return function(request, *args, **kwargs)
            else:
                messages.error(request, "You are not authorized to access this seller page.")
                return redirect('shop:dashboard')
        except Exception as e:
            messages.error(request,
                           "An error occurred while checking seller status. Please complete your profile or contact support.")
            return redirect('shop:customer_profile')

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


# --- Product Catalog Views ---
def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True).select_related('seller', 'category')

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    context = {
        'category': category,
        'categories': categories,
        'products': products,
        'cart_item_count': get_cart_item_count(request)
    }
    return render(request, 'shop/product/list.html', context)


def product_detail(request, id, slug):
    product = get_object_or_404(Product.objects.select_related('seller', 'category'),
                                id=id, slug=slug, available=True)
    context = {
        'product': product,
        'cart_item_count': get_cart_item_count(request)
    }
    return render(request, 'shop/product/detail.html', context)


# --- Utility function to get or create cart ---
def _get_or_create_cart(request):
    customer = None
    order = None
    if request.user.is_authenticated:
        try:
            customer, created = Customer.objects.get_or_create(
                user=request.user,
                defaults={
                    'name': request.user.get_full_name() or request.user.username,
                    'email': request.user.email
                }
            )
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
        except AttributeError:
            pass

    if not order:
        cart_id = request.session.get('cart_id')
        if cart_id:
            try:
                order = Order.objects.get(id=cart_id, complete=False, customer__isnull=True)
            except Order.DoesNotExist:
                order = Order.objects.create(complete=False)
                request.session['cart_id'] = order.id
        else:
            order = Order.objects.create(complete=False)
            request.session['cart_id'] = order.id
    return order


# --- Cart Management Views ---
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    order = _get_or_create_cart(request)
    quantity_to_add = int(request.POST.get('quantity', 1))

    if quantity_to_add <= 0:
        messages.error(request, "Quantity must be a positive number.")
        return redirect(
            request.META.get('HTTP_REFERER', reverse('shop:product_detail', args=[product.id, product.slug])))

    cart_item, created = OrderItem.objects.get_or_create(order=order, product=product)

    if created:
        if quantity_to_add > product.stock:
            cart_item.quantity = product.stock
            messages.warning(request,
                             f"Only {product.stock} {product.name}(s) available. Quantity adjusted in your cart.")
        else:
            cart_item.quantity = quantity_to_add
            messages.success(request, f"{cart_item.quantity} x {product.name} added to your cart.")
    else:
        potential_total_quantity = cart_item.quantity + quantity_to_add
        if potential_total_quantity > product.stock:
            actual_can_add = product.stock - cart_item.quantity
            if actual_can_add > 0:
                cart_item.quantity = product.stock
                messages.warning(request,
                                 f"Only {actual_can_add} more {product.name}(s) could be added due to stock limits. Total in cart now: {cart_item.quantity}.")
            else:
                messages.info(request,
                              f"Cannot add more {product.name}(s). Stock limit of {product.stock} already reached or exceeded in your cart (Current: {cart_item.quantity}).")
        else:
            cart_item.quantity = potential_total_quantity
            messages.success(request,
                             f"{quantity_to_add} more {product.name}(s) added. Total in cart now: {cart_item.quantity}.")

    cart_item.save()
    return redirect('shop:cart_detail')


@require_POST
def remove_from_cart(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id)
    current_cart = _get_or_create_cart(request)
    if order_item.order == current_cart:
        product_name = order_item.product.name
        order_item.delete()
        messages.info(request, f"'{product_name}' removed from your cart.")
    else:
        messages.error(request, "Invalid item or action.")
        return HttpResponseBadRequest("Invalid item.")
    return redirect('shop:cart_detail')


@require_POST
def update_cart_item_quantity(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id)
    current_cart = _get_or_create_cart(request)
    if order_item.order != current_cart:
        messages.error(request, "Invalid item or action.")
        return HttpResponseBadRequest("Invalid item.")

    try:
        quantity = int(request.POST.get('quantity', 0))
    except ValueError:
        messages.error(request, "Invalid quantity format.")
        return redirect('shop:cart_detail')

    if quantity <= 0:
        product_name = order_item.product.name
        order_item.delete()
        messages.info(request, f"'{product_name}' removed from cart as quantity was set to zero or less.")
    elif quantity > order_item.product.stock:
        order_item.quantity = order_item.product.stock
        order_item.save()
        messages.warning(request,
                         f"Quantity for '{order_item.product.name}' adjusted to {order_item.product.stock} (max available stock).")
    else:
        order_item.quantity = quantity
        order_item.save()
        messages.success(request, f"Quantity for '{order_item.product.name}' updated to {quantity}.")
    return redirect('shop:cart_detail')


def cart_detail(request):
    order = _get_or_create_cart(request)
    items = order.items.all().select_related('product') if order else []
    context = {
        'order': order,
        'items': items,
        'cart_item_count': order.get_cart_items if order else 0
    }
    return render(request, 'shop/cart_detail.html', context)


def get_cart_item_count(request):
    order = _get_or_create_cart(request)
    return order.get_cart_items if order else 0


# --- Checkout Views ---
@login_required
def checkout(request):
    order = _get_or_create_cart(request)
    if not order or not order.items.exists():
        messages.info(request, "Your cart is empty. Please add items before proceeding to checkout.")
        return redirect('shop:cart_detail')

    customer = get_object_or_404(Customer, user=request.user)

    shipping_address_instance = ShippingAddress.objects.filter(customer=customer, order=order).first()
    if not shipping_address_instance:
        shipping_address_instance = ShippingAddress.objects.filter(customer=customer).last()

    if request.method == 'POST':
        form = ShippingAddressForm(request.POST,
                                   instance=shipping_address_instance if shipping_address_instance and shipping_address_instance.pk else None)
        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.customer = customer
            shipping_address.order = order
            shipping_address.save()
            messages.success(request, "Shipping address confirmed. Please review your order.")
            return redirect(reverse('shop:order_confirmation', kwargs={'order_id': order.id}))
        else:
            messages.error(request, "Please correct the errors in the shipping address form.")
    else:
        form = ShippingAddressForm(instance=shipping_address_instance if shipping_address_instance else None)

    context = {
        'order': order,
        'items': order.items.all().select_related('product'),
        'shipping_form': form,
        'cart_item_count': order.get_cart_items
    }
    return render(request, 'shop/checkout.html', context)


@login_required
def order_confirmation(request, order_id):
    customer = get_object_or_404(Customer, user=request.user)
    order = get_object_or_404(Order, id=order_id, customer=customer)

    if not order.complete:
        messages.success(request, f"Thank you! Your order #{order.id} has been received and is being processed.")

    context = {
        'order': order,
        'items': order.items.all().select_related('product'),
        'cart_item_count': 0
    }
    return render(request, 'shop/order_confirmation.html', context)


# --- User/Customer Management Views ---
def customer_register(request):
    if request.user.is_authenticated:
        return redirect('shop:dashboard')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Customer.objects.create(user=user,
                                    name=f"{user.first_name} {user.last_name}".strip() or user.username,
                                    email=user.email)
            login(request, user)
            messages.success(request, f"Registration successful! Welcome, {user.username}.")
            return redirect('shop:dashboard')
        else:
            messages.error(request, "Registration unsuccessful. Please correct the errors below.")
    else:
        form = CustomerRegistrationForm()
    context = {'form': form, 'cart_item_count': get_cart_item_count(request)}
    return render(request, 'registration/register.html', context)


@login_required
def customer_profile(request):
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        defaults={'name': request.user.get_full_name() or request.user.username, 'email': request.user.email}
    )

    if request.method == 'POST':
        user_form_submitted = 'update_user_details' in request.POST
        profile_form_submitted = 'update_profile_info' in request.POST

        user_form = UserUpdateForm(instance=request.user)
        profile_form = CustomerProfileUpdateForm(instance=customer)

        if user_form_submitted:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Your account details have been updated successfully!')
                return redirect('shop:customer_profile')
            else:
                messages.error(request, 'Could not update account details. Please correct the errors.')

        if profile_form_submitted:
            profile_form = CustomerProfileUpdateForm(request.POST,
                                                     request.FILES if 'image' in CustomerProfileUpdateForm.Meta.fields else None,
                                                     instance=customer)
            if profile_form.is_valid():
                updated_customer_profile = profile_form.save()
                messages.success(request, 'Your profile information has been updated successfully!')
                if updated_customer_profile.is_seller:
                    messages.info(request, "Your seller account is active! You can now manage your store.")
                    # No automatic redirect to seller_dashboard here, user can choose via nav
                return redirect('shop:customer_profile')
            else:
                messages.error(request, 'Could not update profile information. Please correct the errors.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = CustomerProfileUpdateForm(instance=customer)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'customer': customer,
        'cart_item_count': get_cart_item_count(request)
    }
    return render(request, 'shop/customer_profile.html', context)


@login_required
def order_history(request):
    customer = get_object_or_404(Customer, user=request.user)
    orders = Order.objects.filter(customer=customer, complete=True).order_by('-date_ordered').prefetch_related(
        'items__product')
    context = {
        'orders': orders,
        'customer': customer,
        'cart_item_count': get_cart_item_count(request)
    }
    return render(request, 'shop/order_history.html', context)


# --- Dashboard View (Main Homepage) ---
@login_required
def dashboard_view(request):
    """
    This view now ALWAYS renders the standard customer dashboard.
    Sellers will access their specific dashboard via a separate link.
    """
    current_user = request.user

    customer, created = Customer.objects.get_or_create(
        user=current_user,
        defaults={'name': current_user.get_full_name() or current_user.username, 'email': current_user.email}
    )

    # Removed the automatic redirect to seller_dashboard
    # if customer.is_seller:
    #     return redirect('shop:seller_dashboard')

    categories = Category.objects.all()
    last_order = None
    total_completed_orders = 0
    active_cart_summary = None

    if customer:
        last_order = Order.objects.filter(customer=customer, complete=True).order_by('-date_ordered').first()
        total_completed_orders = Order.objects.filter(customer=customer, complete=True).count()

        active_cart = Order.objects.filter(customer=customer, complete=False).first()
        if active_cart and active_cart.items.exists():
            active_cart_summary = {
                'item_count': active_cart.get_cart_items,
                'total_value': active_cart.get_cart_total
            }

    context = {
        'cart_item_count': get_cart_item_count(request),
        'current_user': current_user,
        'categories': categories,
        'last_order': last_order,
        'total_completed_orders': total_completed_orders,
        'active_cart_summary': active_cart_summary
    }
    return render(request, 'shop/dashboard.html', context)  # Renders the customer dashboard


# --- Seller Specific Views ---
@seller_required
def seller_dashboard(request):
    seller_products = Product.objects.filter(seller=request.user).order_by('-created_at')
    context = {
        'seller_products': seller_products,
        'cart_item_count': get_cart_item_count(request)
    }
    return render(request, 'shop/seller/seller_dashboard.html', context)


@seller_required
def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            slug_candidate = form.cleaned_data.get('slug') or slugify(product.name)
            product.slug = slug_candidate

            original_slug = product.slug
            counter = 1
            while Product.objects.filter(seller=request.user, slug=product.slug).exists():
                product.slug = f"{original_slug}-{counter}"
                counter += 1

            product.save()
            messages.success(request, f"Product '{product.name}' created successfully!")
            return redirect('shop:seller_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm()
    context = {
        'form': form,
        'form_title': 'Create New Product',
        'cart_item_count': get_cart_item_count(request)
    }
    return render(request, 'shop/seller/product_form.html', context)


@seller_required
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            updated_product = form.save(commit=False)
            slug_candidate = form.cleaned_data.get('slug') or slugify(updated_product.name)
            updated_product.slug = slug_candidate

            original_slug = updated_product.slug
            counter = 1
            queryset = Product.objects.filter(seller=request.user, slug=updated_product.slug).exclude(pk=product.pk)
            while queryset.exists():
                updated_product.slug = f"{original_slug}-{counter}"
                counter += 1
                queryset = Product.objects.filter(seller=request.user, slug=updated_product.slug).exclude(pk=product.pk)

            updated_product.save()
            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('shop:seller_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm(instance=product)
    context = {
        'form': form,
        'form_title': f'Update Product: {product.name}',
        'product': product,
        'cart_item_count': get_cart_item_count(request)
    }
    return render(request, 'shop/seller/product_form.html', context)


@seller_required
@require_POST
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    product_name = product.name
    product.delete()
    messages.success(request, f"Product '{product_name}' has been deleted.")
    return redirect('shop:seller_dashboard')


# --- Gemini AI Integration View ---
@seller_required
@require_GET
def generate_product_description_ajax(request):
    product_name = request.GET.get('product_name', '')
    category_name = request.GET.get('category_name', '')
    if not product_name:
        return JsonResponse({'error': 'Product name is required.'}, status=400)
    return JsonResponse({'message': 'Endpoint ready for client-side Gemini call.'})


# --- About Page View ---
def about_page_view(request):
    context = {
        'cart_item_count': get_cart_item_count(request)
    }
    return render(request, 'shop/about_page.html', context)
