# Generated by Django 3.2.15 on 2023-01-12 03:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0038_order_orderitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='address',
            field=models.CharField(max_length=250, null=True, verbose_name='Адрес'),
        ),
    ]