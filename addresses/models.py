from django.db import models
from django.utils import timezone


class Place(models.Model):
    address = models.CharField('Адрес', max_length=100, unique=True)
    lat = models.FloatField('Широта')
    lon = models.FloatField('Долгота')
    last_updated = models.DateTimeField(
        'Время последнего обновления',
        default=timezone.now
    )

    class Meta:
        verbose_name = 'Адрес'
        verbose_name_plural = 'Адреса'

    def __str__(self):
        return self.address

    def get_coordinates(self):
        return float(self.lat), float(self.lon)
