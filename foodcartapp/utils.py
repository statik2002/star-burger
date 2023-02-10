import requests


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lat, lon


def restaurants_serializer(restaurant):
    return {
        'name': restaurant.name,
        'available_products': [
            menu_item.product.name for menu_item in restaurant.menu_items.all() if menu_item.availability],
        'id': restaurant.pk,
        'address': restaurant.address,
    }
