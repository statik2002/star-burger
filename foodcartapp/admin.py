from django.contrib import admin
from django.db import transaction
from django.forms import NumberInput
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme

from star_burger import settings
from .models import Product, Order, OrderItem
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html(
            '<img src="{url}" style="max-height: 200px;"/>',
            url=obj.image.url
        )
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html(
            '<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>',
            edit_url=edit_url,
            src=obj.image.url
        )
    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass


class OrderItemAdmin(admin.TabularInline):
    model = OrderItem

    extra = 1

    fields = ('product', 'quantity', 'get_product_price', 'price')
    readonly_fields = ('get_product_price', )

    @admin.display(description='Цена в каталоге')
    def get_product_price(self, obj):
        return obj.product.price

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'quantity':
            kwargs['widget'] = NumberInput(attrs={'min': '1'})
        return super(
            OrderItemAdmin, self).formfield_for_dbfield(db_field, **kwargs)


def restaurants_serializer(restaurants):

    serialized_restaurants = []

    for restaurant in restaurants:
        serialized_restaurants.append(
            {
                'name': restaurant.name,
                'available_products': [
                    menu_item.product.name for menu_item in restaurant.menu_items.all() if menu_item.availability
                ],
                'id': restaurant.pk,
                'address': restaurant.address,
            }
        )

    return serialized_restaurants


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemAdmin]

    list_display = ('id',
                    'lastname',
                    'firstname',
                    'phonenumber',
                    'status'
                    )

    @transaction.atomic
    def save_formset(self, request, form, formset, change):
        inline_instances = formset.save(commit=False)
        form_instance = form.save(commit=False)

        for obj in formset.deleted_objects:
            obj.delete()

        if not inline_instances:
            for instance in inline_instances:
                instance.price = Product.objects.get(instance).price
                instance.save()
        else:
            for instance in inline_instances:
                instance.price = instance.price
                instance.save()

        if form_instance.production_restaurant:
            form_instance.status = 'AS'

        formset.save_m2m()
        form_instance.save()

    def response_change(self, request, obj):
        res = super(OrderAdmin, self).response_change(request, obj)

        if 'next' in request.GET and url_has_allowed_host_and_scheme(
            request.GET['next'],
            settings.ALLOWED_HOSTS,
            require_https=False
        ):
            return HttpResponseRedirect(request.GET['next'])
        else:
            return res

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not db_field.name == "production_restaurant":
            return super().formfield_for_foreignkey(
                db_field, request, **kwargs
            )

        if not request.resolver_match.kwargs.get('object_id'):
            return super().formfield_for_foreignkey(
                db_field,
                request,
                **kwargs
            )

        order = Order.objects.prefetch_related('order_items__product').get(
            pk=request.resolver_match.kwargs.get('object_id')
        )
        items_in_order = {
            order_item.product.name for order_item in order.order_items.all()
        }
        restaurants = Restaurant.objects.prefetch_related(
            'menu_items__product'
        ).all()
        serialized_restaurants = restaurants_serializer(restaurants)

        restaurants_ids = []
        for restaurant in serialized_restaurants:
            if items_in_order.issubset(restaurant['available_products']):
                restaurants_ids.append(restaurant['id'])

        selected_restaurant = Restaurant.objects.filter(id__in=restaurants_ids)
        kwargs["queryset"] = selected_restaurant

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
