# Generated by Django 3.2.6 on 2021-11-17 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_alter_personaldata_work_loss_insurance_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordercreditproduct',
            name='required_fields',
            field=models.TextField(null=True, verbose_name='Недостающие поля'),
        ),
    ]