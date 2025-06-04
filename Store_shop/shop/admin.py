
from django.contrib import admin
from .models import Customer, Category, Product, Order, OrderItem, ShippingAddress

# Basic registration for Customer
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'email']
    search_fields = ['name', 'email', 'user__username']

# Custom admin for Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)} # Automatically fill slug based on name
    search_fields = ['name']

# Custom admin for Product
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'price', 'stock', 'available', 'created_at', 'updated_at']
    list_filter = ['available', 'created_at', 'updated_at', 'category']
    list_editable = ['price', 'stock', 'available'] # Fields that can be edited directly in the list view
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'category__name']
    date_hierarchy = 'created_at' # Adds date-based navigation

# Inline for OrderItem to be displayed within Order admin
class OrderItemInline(admin.TabularInline): # Or admin.StackedInline for a different layout
    model = OrderItem
    raw_id_fields = ['product'] # Use a simpler input widget for ForeignKey to Product, useful for many products
    extra = 1 # Number of empty forms to display
    # readonly_fields = ['price_at_purchase'] # If you add this field to OrderItem

# Custom admin for Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'date_ordered', 'complete', 'get_cart_total', 'get_cart_items']
    list_filter = ['complete', 'date_ordered']
    search_fields = ['id', 'customer__name', 'customer__email', 'customer__user__username', 'transaction_id']
    inlines = [OrderItemInline] # Embed OrderItem editing within Order
    date_hierarchy = 'date_ordered'
    readonly_fields = ['date_ordered', 'transaction_id'] # Fields that shouldn't be edited manually

    # You might want to add actions here, e.g., "Mark as complete"

# Basic registration for ShippingAddress (often managed alongside Order)
@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['customer', 'order', 'address', 'city', 'zipcode', 'country']
    search_fields = ['customer__name', 'order__id', 'address', 'city', 'zipcode']

# Note: OrderItem is managed via OrderAdmin's inlines, so direct registration is often not needed.
# If you want to access OrderItems directly:
# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ['order', 'product', 'quantity', 'date_added']
#     search_fields = ['order__id', 'product__name']

