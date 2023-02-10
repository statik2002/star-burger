
def restaurants_serializer(restaurant):
    return {
        'name': restaurant.name,
        'available_products': [
            menu_item.product.name for menu_item in restaurant.menu_items.all() if menu_item.availability],
        'id': restaurant.pk,
        'address': restaurant.address,
    }
