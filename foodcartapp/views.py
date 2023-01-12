import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, Http404
from django.templatetags.static import static
from phonenumber_field.phonenumber import PhoneNumber
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

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


@api_view(['POST'])
def register_order(request):

    try:
        order_raw = request.data

        order = Order.objects.create(
            name=order_raw['firstname'],
            surname=order_raw['lastname'],
            phone_number=PhoneNumber.from_string(order_raw['phonenumber']),
            address=order_raw['address']
        )

        if not order_raw['products']:
            order.delete()
            return Response({
                'error': 'Product is empty',
            }, status=status.HTTP_200_OK)

        for product in order_raw['products']:
            try:
                item = Product.objects.get(pk=product['product'])
                order_item = OrderItem.objects.create(
                    item=item,
                    quantity=product['quantity'],
                    order=order
                )
            except ObjectDoesNotExist:
                continue

    except ValueError:
        order.delete()
        return Response({
            'error': 'bla bla bla',
        }, status=status.HTTP_200_OK)
    except TypeError:
        order.delete()
        return Response({
            'error': 'Type error',
        }, status=status.HTTP_200_OK)

    except KeyError:
        order.delete()
        return Response({
            'error': 'No products',
        }, status=status.HTTP_200_OK)

    return JsonResponse({})
