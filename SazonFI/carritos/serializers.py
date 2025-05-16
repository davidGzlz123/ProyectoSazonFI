# carritos/serializers.py
from rest_framework import serializers
from .models import Carrito, ItemCarrito, Pedido, ItemPedido
from productos.models import Producto 
from negocios.models import Negocio
from negocios.serializers import NegocioSerializer 

class ProductoDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'precio'] 

class ItemCarritoSerializer(serializers.ModelSerializer):
    producto = ProductoDetalleSerializer(read_only=True) 
    negocio = NegocioSerializer(read_only=True) 

    class Meta:
        model = ItemCarrito
        fields = ['id', 'producto', 'negocio', 'cantidad', 'precio_al_agregar', 'subtotal']
        read_only_fields = ['id', 'precio_al_agregar', 'subtotal']

class CarritoSerializer(serializers.ModelSerializer):
    items = ItemCarritoSerializer(many=True, read_only=True)
    total_carrito = serializers.SerializerMethodField()
    usuario = serializers.StringRelatedField(read_only=True) 

    class Meta:
        model = Carrito
        fields = ['id', 'usuario', 'items', 'creado_en', 'actualizado_en', 'total_carrito']
        read_only_fields = ['usuario', 'creado_en', 'actualizado_en'] 

    def get_total_carrito(self, obj):
        return sum(item.subtotal for item in obj.items.all())

class CrearActualizarItemCarritoSerializer(serializers.ModelSerializer):
    producto_id = serializers.IntegerField() 
    # CAMBIO: Hacer negocio_id requerido
    negocio_id = serializers.IntegerField(required=True, allow_null=False) 

    class Meta:
        model = ItemCarrito
        fields = ['producto_id', 'negocio_id', 'cantidad']

    def validate_producto_id(self, value):
        if not Producto.objects.filter(pk=value).exists():
            raise serializers.ValidationError("El producto especificado no existe.")
        return value
    
    def validate_negocio_id(self, value):
        # 'required=True' ya maneja el caso de que no se envie.
        # Esta validacion asegura que el ID enviado corresponda a un negocio existente.
        if not Negocio.objects.filter(pk=value).exists():
            raise serializers.ValidationError("El negocio especificado no existe.")
        return value

# --- SERIALIZADORES PARA PEDIDO ---
# (El resto de tus serializadores de Pedido e ItemPedido permanecen igual)
class ItemPedidoSerializer(serializers.ModelSerializer):
    producto = ProductoDetalleSerializer(read_only=True) 
    negocio = NegocioSerializer(read_only=True)

    class Meta:
        model = ItemPedido
        fields = [
            'id', 
            'producto', 
            'negocio',  
            'nombre_producto', 
            'precio_unitario_pedido', 
            'cantidad', 
            'subtotal_pedido'
        ]
        read_only_fields = ('nombre_producto', 'precio_unitario_pedido', 'subtotal_pedido')

class PedidoSerializer(serializers.ModelSerializer):
    items_pedido = ItemPedidoSerializer(many=True, read_only=True) 
    usuario = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id', 
            'usuario', 
            'estado', 
            'total_pedido', 
            'creado_en', 
            'actualizado_en', 
            'items_pedido'
        ]
        read_only_fields = ('total_pedido', 'creado_en', 'actualizado_en', 'estado')
