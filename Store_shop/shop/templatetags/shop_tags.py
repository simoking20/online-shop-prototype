# shop/templatetags/shop_tags.py

from django import template
from shop.models import Customer # Assuming your Customer model is in shop.models

register = template.Library()

@register.filter(name='is_seller')
def is_seller(user):
    """
    Template filter to check if a given user is a seller.
    Usage: {% if user|is_seller %} ... {% endif %}
    """
    if user and user.is_authenticated:
        try:
            customer_profile = getattr(user, 'customer_profile', None)
            if customer_profile:
                return customer_profile.is_seller
        except Customer.DoesNotExist: # Should not happen if using OneToOneField correctly with get_or_create
            return False
        except AttributeError: # Handles cases where customer_profile might not be directly on user
            # This might happen if the related name is different or profile doesn't exist
            # For robustness, try fetching Customer directly if user.customer_profile fails
            try:
                customer = Customer.objects.get(user=user)
                return customer.is_seller
            except Customer.DoesNotExist:
                return False # No customer profile means not a seller
    return False

@register.simple_tag(takes_context=True)
def get_cart_item_count_tag(context):
    """
    Template tag to get the cart item count.
    This is an alternative to passing it in every view's context,
    or using a context processor.
    Usage: {% get_cart_item_count_tag as cart_count %} {{ cart_count }}
    """
    request = context.get('request')
    if request:
        # Assuming you have a function like get_cart_item_count(request) in your views
        # or _get_or_create_cart(request).get_cart_items
        # For this example, let's try to replicate the logic simply.
        # This is a simplified version. A context processor is often better for this.
        from shop.views import _get_or_create_cart # Import locally to avoid circular dependency issues
        order = _get_or_create_cart(request)
        return order.get_cart_items if order else 0
    return 0
