# Generated by Django 3.2.15 on 2023-02-10 02:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0064_rename_order_status_order_status'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='called_datetime',
            new_name='called_at',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='delivered_datetime',
            new_name='delivered_at',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='registered_datetime',
            new_name='registered_at',
        ),
    ]