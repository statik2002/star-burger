from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Count, Prefetch, Aggregate, F, Sum
from django.utils import timezone
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

    item = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='products', verbose_name='Продукт')
    quantity = models.IntegerField('Количество')
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_items')
    price = models.DecimalField('Цена продукта', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def clean(self):
        if self.price is None:
            self.price = self.item.price


def restaurants_serializer(restaurants):

    serialized_restaurants = []

    for restaurant in restaurants:
        serialized_restaurants.append(
            {
                'name': restaurant.name,
                'available_products': [menu_item.product.name for menu_item in restaurant.menu_items.all() if menu_item.availability]
            }
        )

    return serialized_restaurants


class OrderQuerySet(models.QuerySet):

    def calc_order(self):
        return self.prefetch_related('order_items').annotate(
            total=Sum(F('order_items__quantity') * F('order_items__price'))
        )

    def select_restaurants(self):

        restaurants = Restaurant.objects.prefetch_related('menu_items__product').all()
        serialized_restaurants = restaurants_serializer(restaurants)

        for order in self:
            available_restaurants = []
            order_items_raw = {order_item.item.name for order_item in order.order_items.all()}
            for restaurant in serialized_restaurants:
                if order_items_raw.issubset(restaurant['available_products']):
                    available_restaurants.append(restaurant)

            order.available_restaurants = available_restaurants

        return self


class Order(models.Model):

    ORDER_STATUS_CHOICES = [
        ('AC', 'Принят'),
        ('AS', 'Сборка'),
        ('DE', 'Доставка'),
        ('CO', 'Выполнено'),
    ]

    ORDER_PAYMENT_CHOICES = [
        ('CA', 'Наличка'),
        ('EL', 'Электронно'),
    ]

    firstname = models.CharField('Имя', max_length=100, db_index=True)
    lastname = models.CharField('Фамилия', max_length=200, db_index=True)
    phonenumber = PhoneNumberField(max_length=12)
    address = models.CharField('Адрес', max_length=250, default='')
    order_status = models.CharField('Статус заказа', max_length=3, choices=ORDER_STATUS_CHOICES, default='AC', db_index=True)
    comment = models.TextField('Комментарий к заказу', blank=True)
    registered_datetime = models.DateTimeField('Время регистрации заказа', default=timezone.now, db_index=True)
    called_datetime = models.DateTimeField('Время звонка', blank=True, null=True, db_index=True)
    delivered_datetime = models.DateTimeField('Время доставки', blank=True, null=True, db_index=True)
    payment_type = models.CharField('Тип оплаты', max_length=3, choices=ORDER_PAYMENT_CHOICES, default='CA', db_index=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    objects = OrderQuerySet.as_manager()

    def __str__(self):
        return f'{self.firstname} {self.lastname} ({str(self.phonenumber)})'


