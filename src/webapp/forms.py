from django.forms import ModelForm, CharField, Textarea, TextInput, DateField, DateInput
from .models import *


class NewOrderForm(ModelForm):
    estimated_delivery_date = DateField(widget=DateInput(attrs={'type': 'date'}), required=False)
    invoice_date = DateField(widget=DateInput(attrs={'type': 'date'}), required=False)

    def __init__(self, *args, **kwargs):
        super(NewOrderForm, self).__init__(*args, **kwargs)
        try:
            default_status = Status.objects.first()
        except Status.DoesNotExist:
            default_status = None
        self.fields['status'].initial = default_status
        tailwind_class = "resize-y block p-2.5 w-full text-gray-900 bg-gray-50 rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'"
        for field_name, field in self.fields.items():
                field.widget.attrs.update({'class': tailwind_class})

    class Meta:
        model = Order
        fields = ("label", "comments", "status", "estimated_delivery_date", "invoice_date",)



class NewCustomerForm(ModelForm):
    phone_number = PhoneNumberField(region='FR')

    def __init__(self, *args, **kwargs):
        super(NewCustomerForm, self).__init__(*args, **kwargs)
        tailwind_class = "resize-y block p-2.5 w-full text-gray-900 bg-gray-50 rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'"
        for field_name, field in self.fields.items():
                field.widget.attrs.update({'class': tailwind_class})

    class Meta:
        model = Customer
        fields = ("id", "first_name", "last_name", "phone_number", "address", "mail", "comments",)


class AddProductsToOrder(ModelForm):
    def __init__(self, *args, **kwargs):
        super(AddProductsToOrder, self).__init__(*args, **kwargs)
        tailwind_class = "resize-y block p-2.5 w-full text-gray-900 bg-gray-50 rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'"
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': tailwind_class})

    class Meta:
        model = Product
        fields = ("reference", "label", "brand", "supplier", "purchase_price_unit", "selling_price_unit", "quantity")


class AddProductForm(ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
