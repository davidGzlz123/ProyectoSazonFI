from django.contrib import admin
from carritos.models import Pedido, ItemPedido  # Importa Pedido e ItemPedido desde .models

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1
