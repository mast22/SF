# Generated by Django 3.2.6 on 2021-08-27 12:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_initial'),
        ('misc', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='NewAccordance',
            new_name='Accordance',
        ),
    ]
