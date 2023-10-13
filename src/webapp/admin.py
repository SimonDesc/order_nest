from django.contrib import admin
from .models import Customer, Status, Product, Order, OrderHasProduct

admin.site.register(Customer)
admin.site.register(Status)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderHasProduct)