# carritos/serializers.py
from rest_framework import serializers
from .models import Carrito, ItemCarrito, Pedido, ItemPedido
from productos.models import Producto 
from negocios.models import Negocio
from negocios.serializers import NegocioSerializer # Asegurate que NegocioSerializer este definido e importado correctamente
from django.contrib.auth import get_user_model

User = get_user_model()
DEFAULT_PLACEHOLDER_PRODUCTO_IMG = 'https://placehold.co/100x100/EFEFEF/AAAAAA?text=S/I'

class ClientePedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email'] # Ajusta segun los campos de tu modelo User

    def to_representation(self, instance):
        if instance is None:
            return {'id': None, 'username': 'Usuario Eliminado', 'email': ''}
        return super().to_representation(instance)

class PedidoInfoEnItemSerializer(serializers.ModelSerializer):
    usuario = ClientePedidoSerializer(read_only=True)
    class Meta:
        model = Pedido
        fields = ['id', 'estado', 'creado_en', 'usuario', 'total_pedido']

class ProductoDetalleSerializer(serializers.ModelSerializer):
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'precio', 'imagen_url'] # Asegurate que Producto tenga get_imagen_url()

    def get_imagen_url(self, obj):
        if obj is None: 
            return DEFAULT_PLACEHOLDER_PRODUCTO_IMG
        
        request = self.context.get('request')
        model_imagen_url = obj.get_imagen_url() 
        
        if request and model_imagen_url and not model_imagen_url.startswith(('http://', 'https://')):
            return request.build_absolute_uri(model_imagen_url)
        return model_imagen_url if model_imagen_url else DEFAULT_PLACEHOLDER_PRODUCTO_IMG

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
        return sum(item.subtotal for item in obj.items.all() if item.subtotal is not None)

class CrearActualizarItemCarritoSerializer(serializers.ModelSerializer):
    producto_id = serializers.IntegerField() 
    negocio_id = serializers.IntegerField(required=True, allow_null=False) 
    class Meta:
        model = ItemCarrito
        fields = ['producto_id', 'negocio_id', 'cantidad']
    def validate_producto_id(self, value):
        if not Producto.objects.filter(pk=value).exists():
            raise serializers.ValidationError("El producto especificado no existe.")
        return value
    def validate_negocio_id(self, value):
        if not Negocio.objects.filter(pk=value).exists():
            raise serializers.ValidationError("El negocio especificado no existe.")
        return value

class ItemPedidoSerializer(serializers.ModelSerializer):
    producto = ProductoDetalleSerializer(read_only=True, allow_null=True) 
    negocio = NegocioSerializer(read_only=True, allow_null=True)
    pedido = PedidoInfoEnItemSerializer(read_only=True)

    class Meta:
        model = ItemPedido
        fields = [
            'id', 'pedido', 'producto', 'negocio',  
            'nombre_producto', 'precio_unitario_pedido', 
            'cantidad', 'subtotal_pedido'
        ]
        read_only_fields = ('nombre_producto', 'precio_unitario_pedido', 'subtotal_pedido')

class PedidoSerializer(serializers.ModelSerializer): 
    items_pedido = ItemPedidoSerializer(many=True, read_only=True) 
    usuario = ClientePedidoSerializer(read_only=True) 
    class Meta:
        model = Pedido
        fields = [
            'id', 'usuario', 'estado', 'total_pedido', 
            'creado_en', 'actualizado_en', 'items_pedido'
        ]
        read_only_fields = ('total_pedido', 'creado_en', 'actualizado_en') # Estado es actualizable