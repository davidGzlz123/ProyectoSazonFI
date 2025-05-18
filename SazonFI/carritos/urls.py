# carritos/urls.py
from django.urls import path
from . import views 

app_name = 'carritos' 

urlpatterns = [
    path('', views.vista_carrito, name='ver_carrito'), 
    path('mis-pedidos/', views.vista_mis_pedidos, name='mis_pedidos_pagina'), 
]
