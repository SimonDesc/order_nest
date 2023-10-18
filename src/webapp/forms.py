from django.forms import ModelForm, RegexField
from .models import *


class NewOrderForm(ModelForm):
    class Meta:
        model = Order
        fields = ("label", "comments", "status", "estimated_delivery_date", "invoice_date",)


class NewCustomerForm(ModelForm):
    phone_number = PhoneNumberField(region='FR')

    class Meta:
        model = Customer
        fields = ("id", "first_name", "last_name", "phone_number", "address", "mail", "comments",)


class AddProductsToOrder(ModelForm):
    class Meta:
        model = Product
        fields = ("reference", "label", "brand", "supplier", "purchase_price_unit", "selling_price_unit", "quantity")


class AddProductForm(ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
