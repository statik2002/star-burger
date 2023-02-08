from django.urls import path
from django.shortcuts import redirect

from . import views

app_name = "addresses"

urlpatterns = [
    path('', views.index, name='index'),
]
