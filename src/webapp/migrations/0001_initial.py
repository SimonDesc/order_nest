# Generated by Django 4.2.7 on 2024-01-12 10:24

from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=45, verbose_name='prénom')),
                ('last_name', models.CharField(max_length=45, verbose_name='nom')),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region='FR', verbose_name='téléphone')),
                ('address', models.CharField(blank=True, max_length=200, verbose_name='adresse')),
                ('mail', models.EmailField(blank=True, max_length=45)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('comments', models.TextField(blank=True, max_length=2000, verbose_name='commentaire')),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('estimated_delivery_date', models.DateField(blank=True, null=True, verbose_name='date de livraison')),
                ('invoice_date', models.DateField(blank=True, null=True, verbose_name='date de facturation')),
                ('label', models.CharField(default='', max_length=45, verbose_name='libellé')),
                ('comments', models.TextField(blank=True, max_length=2000, verbose_name='commentaire')),
                ('status', models.CharField(choices=[('En attente', 'En attente'), ('En cours', 'En cours'), ('Terminée', 'Terminée'), ('Facturée', 'Facturée'), ('Annulée', 'Annulée'), ('Urgent', 'Urgent')], default='En cours', max_length=32)),
                ('active', models.BooleanField(default=True)),
                ('payment', models.CharField(choices=[('En attente', 'En attente'), ('Réglé', 'Réglé')], default='En attente', max_length=32, verbose_name='Etat paiement')),
                ('payment_method', models.CharField(blank=True, choices=[('Carte bancaire', 'Carte bancaire'), ('Espèce', 'Espèce'), ('Chèque', 'Chèque'), ('Virement', 'Virement')], max_length=32, verbose_name='Mode de paiement')),
                ('customer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='webapp.customer')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=45, verbose_name='libellé *')),
                ('size', models.CharField(blank=True, max_length=45, verbose_name='dimension')),
                ('wand', models.CharField(blank=True, max_length=45, verbose_name='baguette')),
                ('glass', models.CharField(choices=[('Artglass', 'Artglass'), ('Normal', 'Normal'), ('Anti-reflet', 'Anti-reflet'), ('PMMA', 'PMMA'), ('Sans', 'Sans')], default='Sans', max_length=45, verbose_name='verre')),
                ('mat', models.CharField(blank=True, max_length=45, verbose_name='passe-partout')),
                ('mesh', models.CharField(blank=True, max_length=45, verbose_name='filet')),
                ('selling_price_unit', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='prix de vente')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='OrderHasProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('order', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='webapp.order')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='webapp.product', verbose_name='produit')),
            ],
        ),
        migrations.CreateModel(
            name='OrderAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='order_attachments/')),
                ('canvas_json', models.JSONField(null=True)),
                ('type', models.CharField(blank=True, max_length=45)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='webapp.order')),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='products',
            field=models.ManyToManyField(through='webapp.OrderHasProduct', to='webapp.product'),
        ),
    ]
