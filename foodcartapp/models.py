from geopy import distance
from operator import itemgetter
from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import F, Sum
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from addresses.models import Place
from foodcartapp.serializer import restaurants_serializer
from addresses.yandex_geo_api import fetch_coordinates
from star_burger import settings


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
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='order_items',
        verbose_name='Продукт'
    )
    quantity = models.IntegerField(
        'Количество',
        validators=[MinValueValidator(1)]
    )
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ'
    )
    price = models.DecimalField(
        'Цена продукта',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True
    )

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def clean(self):
        if self.price is None:
            self.price = self.product.price


class OrderQuerySet(models.QuerySet):

    def get_amount(self):
        return self.annotate(
            total=Sum(F('items__quantity') * F('items__price'))
        )

    def select_restaurants(self):

        restaurants = Restaurant.objects.prefetch_related(
            'menu_items__product'
        ).prefetch_related('orders')
        serialized_restaurants = [
            restaurants_serializer(restaurant) for restaurant in restaurants
        ]

        places = Place.objects.filter(
            address__in=[restaurant['address'] for restaurant in serialized_restaurants]+[order.address for order in self]
        )

        for order in self:
            available_restaurants = []
            items_in_order = {
                order_item.product.name for order_item in order.items.all()
            }
            for restaurant in serialized_restaurants:
                if not items_in_order.issubset(
                    restaurant['available_products']
                ):
                    continue

                order_place = list(
                    filter(
                        lambda place: (place.address == order.address),
                        places
                    )
                )
                order_place = order_place[0]

                restaurant_place = list(
                    filter(
                        lambda place: (
                            place.address == restaurant['address']
                        ),
                        places
                    )
                )

                restaurant['distance'] = int(
                    distance.distance(
                        order_place.get_coordinates(),
                        restaurant_place[0].get_coordinates()
                    ).km
                )
                available_restaurants.append(restaurant)

            order.available_restaurants = sorted(
                available_restaurants,
                key=itemgetter('distance'),
                reverse=True
            )

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
        ('DF', 'Не определено')
    ]

    firstname = models.CharField('Имя', max_length=100, db_index=True)
    lastname = models.CharField('Фамилия', max_length=200, db_index=True)
    phonenumber = PhoneNumberField('Номер телефона', max_length=12)
    address = models.CharField('Адрес', max_length=250)
    status = models.CharField(
        'Статус заказа',
        max_length=3,
        choices=ORDER_STATUS_CHOICES,
        default='AC',
        db_index=True
    )
    comment = models.TextField('Комментарий к заказу', blank=True)
    registered_at = models.DateTimeField(
        'Время регистрации заказа',
        default=timezone.now,
        db_index=True
    )
    called_at = models.DateTimeField(
        'Время звонка',
        blank=True,
        null=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        'Время доставки',
        blank=True,
        null=True,
        db_index=True
    )
    payment_type = models.CharField(
        'Тип оплаты',
        max_length=3,
        choices=ORDER_PAYMENT_CHOICES,
        default='DF',
        db_index=True
    )
    production_restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='Заказ готовит ресторан',
        on_delete=models.CASCADE,
        related_name='orders',
        blank=True,
        null=True
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.firstname} {self.lastname} ({str(self.phonenumber)})'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        lat, lon = fetch_coordinates(
            settings.YANDEX_GEO_API_KEY,
            self.address
        )
        place_obj, created = Place.objects.update_or_create(
            address=self.address,
            defaults={
                'lat': lat,
                'lon': lon
            }
        )

        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
