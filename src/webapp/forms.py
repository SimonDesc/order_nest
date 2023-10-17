from django.forms import ModelForm
from .models import *
from django_select2 import forms as s2forms


class NewOrderForm(ModelForm):
    class Meta:
        model = Order
        fields = ("label", "comments", "status", "estimated_delivery_date", "invoice_date",)


class NewCustomerForm(ModelForm):
    class Meta:
        model = Customer
        fields = ("first_name", "last_name", "phone_number", "address", "mail",)


class AddProductForm(ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
