# Generated by Django 3.2.15 on 2023-01-31 04:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0050_order_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('AC', 'Принят'), ('AS', 'Сборка'), ('DE', 'Доставка'), ('CO', 'Выполнено')], db_index=True, default='AC', max_length=3, verbose_name='Статус заказа'),
        ),
    ]
