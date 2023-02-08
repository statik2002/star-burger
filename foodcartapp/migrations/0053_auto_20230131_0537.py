# Generated by Django 3.2.15 on 2023-01-31 05:37

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0052_order_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='called_datetime',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Время звонка'),
        ),
        migrations.AddField(
            model_name='order',
            name='delivered_datetime',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Время доставки'),
        ),
        migrations.AddField(
            model_name='order',
            name='registered_datetime',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Время регистрации заказа'),
        ),
    ]