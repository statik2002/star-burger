from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ListField, IntegerField
from rest_framework.response import Response
from rest_framework import status

from rest_framework.serializers import Serializer, ModelSerializer

from addresses.models import Place
from addresses.yandex_geo_api import fetch_coordinates
from star_burger import settings
from .models import Product, Order, OrderItem


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


class OrderItemSerialiser(Serializer):

    product = IntegerField()
    quantity = IntegerField()

    def validate_product(self, value):
        if not value:
            raise ValidationError('Empty prduct id')
        return value

    def validate_quantity(self, value):
        if not value:
            raise ValidationError('Empty product quantity')
        return value


class OrderSerializer(ModelSerializer):

    products = ListField(child=OrderItemSerialiser(), write_only=True)

    class Meta:
        model = Order
        fields = (
            'firstname',
            'lastname',
            'phonenumber',
            'address',
            'products'
        )


@api_view(['POST'])
@transaction.atomic
def register_order(request):

    order_serializer = OrderSerializer(data=request.data)
    order_serializer.is_valid(raise_exception=True)

    order = Order.objects.create(
        firstname=order_serializer.validated_data['firstname'],
        lastname=order_serializer.validated_data['lastname'],
        phonenumber=order_serializer.validated_data['phonenumber'],
        address=order_serializer.validated_data['address']
    )

    lat, lon = fetch_coordinates(
        settings.YANDEX_GEO_API_KEY,
        order_serializer['address']
    )
    place_obj, created = Place.objects.update_or_create(
        address=order.address,
        defaults={
            'lat': lat,
            'lon': lon
        }
    )

    if not order_serializer.validated_data['products']:
        return Response({
            'error': 'Products is empty',
        }, status=status.HTTP_400_BAD_REQUEST)

    order_items = []

    for product_item in order_serializer.validated_data['products']:
        try:
            product = Product.objects.get(pk=product_item['product'])
            order_item = OrderItem(
                product=product,
                quantity=product_item['quantity'],
                order=order,
                price=product.price
            )
            order_items.append(order_item)
        except ObjectDoesNotExist:
            return Response({
                'error': f'Product with code {product_item["product"]}'
                         f' does not exist',
            }, status=status.HTTP_400_BAD_REQUEST)

    OrderItem.objects.bulk_create(order_items)

    return Response(order_serializer.data)
