from django.contrib import admin
from .models import Pedido, ItemPedido  # Importa Pedido e ItemPedido desde .models

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'negocio', 'fecha_pedido', 'estado', 'total']
    list_filter = ['estado', 'negocio']
    search_fields = ['usuario__username', 'negocio__nombre']
    inlines = [ItemPedidoInline]