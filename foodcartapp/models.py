from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Count, Prefetch, Aggregate, F, Sum
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderItem(models.Model):

    item = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='products')
    quantity = models.IntegerField('Количество')
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_items')
    price = models.DecimalField('Цена продукта', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])


class OrderQuerySet(models.QuerySet):

    def calc_order(self):

        return self.prefetch_related('order_items').annotate(total=Sum(F('order_items__quantity') * F('order_items__price')))


class Order(models.Model):

    firstname = models.CharField('Имя', max_length=100, db_index=True)
    lastname = models.CharField('Фамилия', max_length=200, db_index=True)
    phonenumber = PhoneNumberField(max_length=12)
    address = models.CharField('Адрес', max_length=250, default='')

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    objects = OrderQuerySet.as_manager()

    def __str__(self):
        return f'{self.firstname} {self.lastname} {str(self.phonenumber)}'


