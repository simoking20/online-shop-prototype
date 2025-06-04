from django.db import models
from django.contrib.auth.models import User
import uuid
from django.urls import reverse  # For get_absolute_url


# Customer Model
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='customer_profile')
    name = models.CharField(max_length=200, null=True)
    email = models.EmailField(max_length=200, null=True)
    is_seller = models.BooleanField(default=False, help_text="Designates whether this customer can also sell products.")

    # Example: phone_number = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.name if self.name else self.user.username if self.user else "Unnamed Customer"


# Category Model
class Category(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, help_text="Unique URL-friendly identifier for the category.")

    # Optional: created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_categories')

    class Meta:
        ordering = ('name',)
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):  # Useful for linking to category pages
        return reverse('shop:product_list_by_category', args=[self.slug])


# Product Model
class Product(models.Model):
    # Changed: Added null=True, blank=True to allow migration on existing data.
    # Your views should ensure a seller is assigned for new products.
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='products_for_sale',
        help_text="The user selling this product.",
        null=True,  # Allows existing rows to have no seller initially
        blank=True  # Allows form submission without it if handled in view, though our ProductForm doesn't include it
    )
    category = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200,
                            help_text="Unique URL-friendly identifier for the product. Will be auto-generated if left blank by seller.")
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/%Y/%m/%d/', blank=True, null=True,
                              help_text="Upload a product image.")
    stock = models.PositiveIntegerField(default=0, help_text="Available stock quantity.")
    available = models.BooleanField(default=True, help_text="Is the product available for purchase?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['seller']),
        ]
        # If slugs need to be unique per seller:
        # unique_together = (('seller', 'slug'),)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])

    # from django.utils.text import slugify
    # def save(self, *args, **kwargs):
    #     if not self.slug:
    #         self.slug = slugify(self.name)
    #     super().save(*args, **kwargs)


# Order Model
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False, help_text="Is the order complete and processed?")
    transaction_id = models.CharField(max_length=100, null=True, blank=True, unique=True, default=uuid.uuid4)

    class Meta:
        ordering = ('-date_ordered',)

    def __str__(self):
        return f"Order {self.id} by {self.customer.name if self.customer and self.customer.name else (self.customer.user.username if self.customer and self.customer.user else 'Guest')}"

    @property
    def get_cart_total(self):
        orderitems = self.items.all()
        total = sum([item.get_total for item in orderitems])
        return total

    @property
    def get_cart_items(self):
        orderitems = self.items.all()
        total = sum([item.quantity for item in orderitems])
        return total


# OrderItem Model
class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='order_items')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, related_name='items')
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} of {self.product.name if self.product else 'N/A'} in Order {self.order.id if self.order else 'N/A'}"

    @property
    def get_total(self):
        if self.product and self.product.price is not None and self.quantity is not None:
            total = self.product.price * self.quantity
            return total
        return 0


# ShippingAddress Model
class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipping_address')
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Shipping to: {self.address}, {self.city}"

    class Meta:
        verbose_name_plural = "Shipping Addresses"
