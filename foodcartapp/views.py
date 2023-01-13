import json

import django.db.utils
import phonenumbers.phonenumberutil
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, Http404
from django.templatetags.static import static
from phonenumber_field.phonenumber import PhoneNumber
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
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


def validate(order_raw):

    errors = []

    if 'firstname' not in order_raw:
        errors.append('First name is required.')
    if 'lastname' not in order_raw:
        errors.append('Last name is required.')
    if 'phonenumber' not in order_raw:
        errors.append('Phonenumber is required.')
    if 'address' not in order_raw:
        errors.append('Address is required.')
    if 'products' not in order_raw:
        errors.append('Products is required.')

    if errors:
        raise ValidationError(errors)


@api_view(['POST'])
def register_order(request):

    validate(request.data)

    try:
        order_raw = request.data

        firstname = order_raw['firstname']
        surname = order_raw['lastname']
        phone_number = PhoneNumber.from_string(order_raw['phonenumber'])
        address = order_raw['address']
        products = order_raw['products']

        if not isinstance(firstname, str):
            return Response(
                {'error': 'Wrong name'},
                status=status.HTTP_200_OK
            )

        if not isinstance(surname, str):
            return Response(
                {'error': 'Wrong lastname'},
                status=status.HTTP_200_OK
            )

        if not phone_number.is_valid():
            return Response(
                {'error': 'Phone number is invalid'},
                status=status.HTTP_200_OK
            )

        order = Order.objects.create(
            name=firstname,
            surname=surname,
            phone_number=phone_number,
            address=address
        )

        if not products:
            order.delete()
            return Response({
                'error': 'Product is empty',
            }, status=status.HTTP_200_OK)

        for product in products:
            try:
                item = Product.objects.get(pk=product['product'])
                order_item = OrderItem.objects.create(
                    item=item,
                    quantity=product['quantity'],
                    order=order
                )
            except ObjectDoesNotExist:
                order.delete()
                return Response({
                    'error': 'Wrong product',
                }, status=status.HTTP_200_OK)

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
        return Response({
            'error': 'Key error',
        }, status=status.HTTP_200_OK)

    except django.db.utils.IntegrityError:
        return Response(
            {'error': 'Name is null'},
            status=status.HTTP_200_OK
        )
    except phonenumbers.phonenumberutil.NumberParseException:
        return Response(
            {'error': 'Wrong phone number'},
            status=status.HTTP_200_OK
        )

    return JsonResponse({})
