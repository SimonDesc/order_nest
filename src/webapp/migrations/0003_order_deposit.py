# Generated by Django 4.2.7 on 2024-01-13 16:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0002_product_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='deposit',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='acompte'),
        ),
    ]