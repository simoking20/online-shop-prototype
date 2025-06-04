#shop / forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Customer, ShippingAddress, Order, Product, Category  # Ensure all needed models are imported
from django.utils.text import slugify


class CustomerRegistrationForm(UserCreationForm):
    """
    A form for registering new users.
    Inherits from UserCreationForm and adds email, first_name, last_name fields.
    """
    email = forms.EmailField(required=True, help_text='Required. Inform a valid email address.')
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=150, required=False, help_text='Optional.')

    class Meta(UserCreationForm.Meta):
        model = User
        # Ensure all desired fields are included
        fields = ("username", "first_name", "last_name", "email")  # Explicitly list fields for clarity

    def save(self, commit=True):
        """
        Save the provided password in hashed format.
        Ensure email, first_name, and last_name are also saved.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """
    Form for users to update their basic information (excluding password).
    """
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        # Password changes should be handled by a separate form/view.


class CustomerProfileUpdateForm(forms.ModelForm):
    """
    Form for users to update their customer-specific profile information.
    Includes a way to request or indicate seller status.
    """

    # This field allows users to express intent. The actual 'is_seller' might be admin-controlled.
    # For this example, we'll allow direct editing of 'is_seller' for simplicity,
    # but in a real app, you'd likely have a review process.
    # request_seller_status = forms.BooleanField(
    #     required=False,
    #     label="I want to become a seller / Manage my seller status",
    #     help_text="Check this to apply for or manage your seller account."
    # )

    class Meta:
        model = Customer
        fields = ['name', 'email', 'is_seller']  # 'is_seller' is now directly editable
        # If you add more fields to Customer model like phone_number, add them here.
        # Example: fields = ['name', 'email', 'phone_number', 'is_seller']
        widgets = {
            'is_seller': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Add styling for other fields if needed
            'name': forms.TextInput(attrs={'class': 'form-control mb-2'}),
            'email': forms.EmailInput(attrs={'class': 'form-control mb-2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill name and email from User model if they are empty in Customer profile
        if self.instance and self.instance.user:
            if not self.initial.get('name') and self.instance.user.get_full_name():
                self.initial['name'] = self.instance.user.get_full_name()
            if not self.initial.get('email') and self.instance.user.email:
                self.initial['email'] = self.instance.user.email

        # If 'is_seller' should be admin-controlled, you might disable it:
        # self.fields['is_seller'].disabled = True
        # And then handle 'request_seller_status' in your view logic.
        # For this example, making 'is_seller' directly editable.


class ShippingAddressForm(forms.ModelForm):
    """
    Form for collecting shipping address information.
    """

    class Meta:
        model = ShippingAddress
        fields = ['address', 'city', 'state', 'zipcode', 'country']
        # 'customer' and 'order' will be set in the view.
        widgets = {
            'address': forms.TextInput(attrs={'placeholder': '1234 Main St', 'class': 'form-control mb-2'}),
            'city': forms.TextInput(attrs={'placeholder': 'Anytown', 'class': 'form-control mb-2'}),
            'state': forms.TextInput(attrs={'placeholder': 'State/Province', 'class': 'form-control mb-2'}),
            'zipcode': forms.TextInput(attrs={'placeholder': 'Postal Code', 'class': 'form-control mb-2'}),
            'country': forms.TextInput(attrs={'placeholder': 'Country', 'class': 'form-control mb-2'}),
        }


# --- Seller Specific Forms ---
class ProductForm(forms.ModelForm):
    """Form for sellers to create and edit products."""
    # Allow seller to optionally provide a slug, or it can be auto-generated.
    slug = forms.SlugField(required=False,
                           help_text="Optional. If left blank, a slug will be generated from the product name. Use only letters, numbers, underscores, or hyphens.")

    class Meta:
        model = Product
        fields = ['name', 'slug', 'category', 'description', 'price', 'image', 'stock', 'available']
        # 'seller' will be set automatically in the view.
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control mb-2'}),
            'slug': forms.TextInput(attrs={'class': 'form-control mb-2'}),
            'category': forms.Select(attrs={'class': 'form-select mb-2'}),  # Use form-select for Bootstrap
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control mb-2'}),
            'price': forms.NumberInput(attrs={'class': 'form-control mb-2', 'step': '0.01'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control mb-2'}),  # Allows clearing the image
            'stock': forms.NumberInput(attrs={'class': 'form-control mb-2', 'min': '0'}),
            'available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        # Add placeholder or help text if needed
        self.fields['category'].empty_label = "Select a Category"

    def clean_slug(self):
        # If a slug is provided, ensure it's valid.
        # If not provided, it will be generated in the view or model's save method.
        slug = self.cleaned_data.get('slug')
        if slug:
            return slugify(slug)  # Ensure it's a valid slug format
        return slug  # Return None or empty string if not provided by user

# Optional: Form for sellers to create categories (if you implement this feature)
# class CategoryForm(forms.ModelForm):
#     class Meta:
#         model = Category
#         fields = ['name']
#
#     def save(self, commit=True, user=None): # user arg if categories are tied to sellers
#         instance = super().save(commit=False)
#         instance.slug = slugify(instance.name) # Auto-generate slug
#         # if user and hasattr(instance, 'created_by'): # If you add 'created_by' to Category
#         #     instance.created_by = user
#         if commit:
#             instance.save()
#         return instance
