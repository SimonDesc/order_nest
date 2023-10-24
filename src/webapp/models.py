import os

from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Customer(models.Model):
    first_name = models.CharField(max_length=45, null=False, blank=False, verbose_name="prenom")
    last_name = models.CharField(max_length=45, null=False, blank=False, verbose_name="nom")
    phone_number = PhoneNumberField(null=False, blank=False, region="FR")
    address = models.CharField(max_length=200, blank=True)
    mail = models.EmailField(max_length=45, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    comments = models.TextField(max_length=2000, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name} {self.phone_number}'


class Status(models.Model):
    label = models.CharField(max_length=45)
    comments = models.TextField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.label}'


class Product(models.Model):
    reference = models.CharField(max_length=45, blank=True)
    label = models.CharField(max_length=45, verbose_name="libelle")
    brand = models.CharField(max_length=45, blank=True, verbose_name="marque")
    supplier = models.CharField(max_length=45, blank=True, verbose_name="fournisseur")
    purchase_price_unit = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    selling_price_unit = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.reference} {self.label}'


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    estimated_delivery_date = models.DateField(blank=True, null=True, verbose_name="date_livraison")
    invoice_date = models.DateField(blank=True, null=True, verbose_name="date_facturation")
    label = models.CharField(max_length=45, blank=False, default='')
    comments = models.TextField(max_length=2000, blank=True)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    products = models.ManyToManyField(Product, through='OrderHasProduct')
    active = models.BooleanField(default=True)

    @property
    def total_price(self):
        total = 0
        for relation in self.orderhasproduct_set.all():
            total += relation.product.selling_price_unit * relation.product.quantity
        return total

    def __str__(self):
        return f'{self.label} {self.status}'


class OrderHasProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, verbose_name="produit")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.order} {self.product.label}'


class OrderAttachment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to='order_attachments/')

    @property
    def file_name(self):
        if self.file:
            return os.path.basename(self.file.name)
        return None
