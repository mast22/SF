# Generated by Django 3.2.6 on 2021-12-17 14:01

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('banks', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='termancreditproduct',
            name='commission',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5, verbose_name='Комиссия территориала'),
        ),
        migrations.AddField(
            model_name='termanextraservice',
            name='commission',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5, verbose_name='Комиссия территориала'),
        ),
        migrations.AlterField(
            model_name='termancreditproduct',
            name='commission_max',
            field=models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Комиссия агентов. До'),
        ),
        migrations.AlterField(
            model_name='termancreditproduct',
            name='commission_min',
            field=models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Комиссия агентов. От'),
        ),
    ]
