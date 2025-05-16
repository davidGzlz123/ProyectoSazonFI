# carritos/admin.py
from django.contrib import admin
from .models import Carrito, ItemCarrito, Pedido, ItemPedido # AÑADIR Pedido, ItemPedido

# ... (tu ItemCarritoInline y CarritoAdmin existentes) ...

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0 # No mostrar forms vacíos por defecto
    readonly_fields = ('nombre_producto', 'precio_unitario_pedido', 'subtotal_pedido', 'producto', 'negocio')
    can_delete = False # Generalmente no quieres borrar items de un pedido completado desde aquí

    def has_add_permission(self, request, obj=None): # No permitir añadir items desde el admin del pedido
        return False

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'estado', 'total_pedido', 'creado_en')
    list_filter = ('estado', 'creado_en', 'usuario')
    search_fields = ('id', 'usuario__username', 'items_pedido__nombre_producto')
    readonly_fields = ('total_pedido', 'creado_en', 'actualizado_en') # Total se calcula
    inlines = [ItemPedidoInline]

@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'nombre_producto', 'negocio', 'cantidad', 'precio_unitario_pedido', 'subtotal_pedido')
    list_filter = ('pedido__usuario', 'negocio', 'producto')
    search_fields = ('nombre_producto', 'pedido__id')