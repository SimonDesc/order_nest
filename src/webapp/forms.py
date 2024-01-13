from collections.abc import Mapping
from typing import Any
from django.core.files.base import File
from django.db.models.base import Model
from django.forms import ModelForm, CharField, Textarea, TextInput, DateField, DateInput, NumberInput
from django.forms.utils import ErrorList
from .models import *


class NewOrderForm(ModelForm):
    estimated_delivery_date = DateField(
        widget=DateInput(format='%Y-%m-%d', attrs={"type": "date"}),
        label="Date de livraison", 
        required=False,
    )
    invoice_date = DateField(
        widget=DateInput(format='%Y-%m-%d', attrs={"type": "date"}),
        label="Date de facturation",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(NewOrderForm, self).__init__(*args, **kwargs)
        self.label_suffix = ""
        tailwind_class = "resize-y block p-2.5 w-full text-gray-900 bg-gray-50 rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'"
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": tailwind_class})

    class Meta:
        model = Order
        widgets = {
            "comments": Textarea(attrs={"rows": 4, "cols": 25}),
        }
        fields = (
            "label",
            "comments",
            "status",
            "estimated_delivery_date",
            "invoice_date",
            "payment",
            "payment_method",
        )


class NewCustomerForm(ModelForm):
    phone_number = PhoneNumberField(region="FR")

    def __init__(self, *args, **kwargs):
        super(NewCustomerForm, self).__init__(*args, **kwargs)
        self.label_suffix = ""
        tailwind_class = "resize-y block p-2.5 w-full text-gray-900 bg-gray-50 rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'"
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": tailwind_class})

    class Meta:
        model = Customer
        fields = (
            "id",
            "first_name",
            "last_name",
            "phone_number",
            "address",
            "mail",
            "comments",
        )


class AddProductsToOrder(ModelForm):
    
    
    def __init__(self, *args, **kwargs):
        super(AddProductsToOrder, self).__init__(*args, **kwargs)
        
        self.label_suffix = ""
        tailwind_class = "resize-y block p-2.5 w-full text-gray-900 bg-gray-50 rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'"
        checkbox_class = "w-6 h-6 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"

        for field_name, field in self.fields.items():
            if field_name == "status":
                field.widget.attrs.update({"class": checkbox_class})
            else:
                field.widget.attrs.update({"class": tailwind_class})

    class Meta:
        model = Product
        
        fields = (
            "size",
            "label",
            "wand",
            "glass",
            "mat",
            "mesh",
            "selling_price_unit",
            "status",
        )


class AddProductForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(AddProductForm, self).__init__(*args, **kwargs)
        self.label_suffix = ""
        tailwind_class = "resize-y block p-2.5 w-full text-gray-900 bg-gray-50 rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'"
        checkbox_class = "w-6 h-6  text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
        for field_name, field in self.fields.items():
            if field_name == "status":
                field.widget.attrs.update({"class": checkbox_class})
            else:
                field.widget.attrs.update({"class": tailwind_class})

    class Meta:
        model = Product
        fields = (
            "size",
            "label",
            "wand",
            "glass",
            "mat",
            "mesh",
            "selling_price_unit",
            "status",
        )
