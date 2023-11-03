import os

from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Customer(models.Model):
    first_name = models.CharField(max_length=45, null=False, blank=True, verbose_name="prénom")
    last_name = models.CharField(max_length=45, null=False, blank=False, verbose_name="nom")
    phone_number = PhoneNumberField(null=False, blank=False, region="FR", verbose_name="téléphone")
    address = models.CharField(max_length=200, blank=True, verbose_name="adresse")
    mail = models.EmailField(max_length=45, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    comments = models.TextField(max_length=2000, blank=True, verbose_name="commentaire")
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name} {self.phone_number}'


class Product(models.Model):
    reference = models.CharField(max_length=45, blank=True, verbose_name="référence")
    label = models.CharField(max_length=45, verbose_name="libellé")
    brand = models.CharField(max_length=45, blank=True, verbose_name="marque")
    supplier = models.CharField(max_length=45, blank=True, verbose_name="fournisseur")
    purchase_price_unit = models.DecimalField(default=0, max_digits=10, decimal_places=2, verbose_name="prix d'achat")
    selling_price_unit = models.DecimalField(default=0, max_digits=10, decimal_places=2, verbose_name="prix de vente")
    quantity = models.PositiveIntegerField(default=1, blank=False, null=False, verbose_name="quantité")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.reference} {self.label}'


class Order(models.Model):
    STATUS = (
        ('En attente', 'En attente'),
        ('En cours', 'En cours'),
        ('Terminée', 'Terminée'),
        ('Facturée', 'Facturée'),
        ('Annulée', 'Annulée'),
        ('Urgent', 'Urgent'),
    )

    PAIEMENT = (
        ('En attente', 'En attente'),
        ('Réglé', 'Réglé'),
    )

    METHOD = (
        ('Carte bancaire', 'Carte bancaire'),
        ('Espèce', 'Espèce'),
        ('Chèque', 'Chèque'),
        ('Virement', 'Virement'),
    )



    created_at = models.DateTimeField(auto_now_add=True)
    estimated_delivery_date = models.DateField(blank=True, null=True, verbose_name="date de livraison")
    invoice_date = models.DateField(blank=True, null=True, verbose_name="date de facturation")
    label = models.CharField(max_length=45, blank=False, default='', verbose_name="libellé")
    comments = models.TextField(max_length=2000, blank=True, verbose_name="commentaire")
    status = models.CharField(max_length=32, choices=STATUS, default='En attente')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    products = models.ManyToManyField(Product, through='OrderHasProduct')
    active = models.BooleanField(default=True)
    payment = models.CharField(max_length=32, choices=PAIEMENT, verbose_name="Paiment" , default='En attente')
    payment_method = models.CharField(max_length=32, choices=METHOD, verbose_name="Type de paiement", blank=True)

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
    canvas_json = models.JSONField(null=True)
    type = models.CharField(max_length=45, blank=True)

    @property
    def file_name(self):
        if self.file:
            return os.path.basename(self.file.name)
        return None

    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return None
