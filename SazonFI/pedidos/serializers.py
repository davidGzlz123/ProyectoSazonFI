
from rest_framework import serializers
from .models import Pedido, ItemPedido
from productos.serializers import ProductoSerializer  # Importa ProductoSerializer

class ItemPedidoSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)  # Serializa el producto completo
    class Meta:
        model = ItemPedido
        fields = ['id', 'producto', 'cantidad', 'subtotal']

class PedidoSerializer(serializers.ModelSerializer):
    items = ItemPedidoSerializer(many=True, read_only=True)  # Serializa los ítems del pedido
    class Meta:
        model = Pedido
        fields = ['id', 'usuario', 'negocio', 'fecha_pedido', 'estado', 'total', 'items']