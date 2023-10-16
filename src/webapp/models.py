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
    purchase_price_unit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    selling_price_unit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    quantity = models.PositiveIntegerField()
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
    draw_url = models.CharField(max_length=200, blank=True)
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
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="produit")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.order} {self.product.label}'
