# Generated by Django 3.2.6 on 2021-12-17 14:01

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_ordercreditproduct_required_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordercreditproduct',
            name='terman_commission',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=12, verbose_name='Комиссия территориала'),
        ),
        migrations.AddField(
            model_name='orderextraservice',
            name='terman_commission',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=12, verbose_name='Комиссия территориала'),
        ),
    ]
