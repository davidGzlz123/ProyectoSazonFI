# carritos/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction 
import traceback 

from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, APIException # Importar APIException


# Importaciones de Modelos
from .models import Carrito, ItemCarrito, Pedido, ItemPedido
from productos.models import Producto
from negocios.models import Negocio

# Importaciones de Serializadores
from .serializers import (
    ItemCarritoSerializer, 
    CrearActualizarItemCarritoSerializer, 
    CarritoSerializer,
    PedidoSerializer,
)


@login_required 
def vista_carrito(request):
    return render(request, 'carrito/carrito.html')

@login_required
def vista_mis_pedidos(request):
    return render(request, 'carrito/mis_pedidos.html')


class AgregarItemCarritoAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = CrearActualizarItemCarritoSerializer(data=request.data)
        if serializer.is_valid():
            producto_id = serializer.validated_data['producto_id']
            cantidad_solicitada = serializer.validated_data['cantidad']
            negocio_id = serializer.validated_data.get('negocio_id')
            
            carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
            producto = get_object_or_404(Producto, pk=producto_id)
            negocio_instancia = None
            if negocio_id:
                negocio_instancia = get_object_or_404(Negocio, pk=negocio_id)
            
            item_carrito, creado = ItemCarrito.objects.get_or_create(
                carrito=carrito,
                producto=producto,
                negocio=negocio_instancia, 
                defaults={
                    'cantidad': cantidad_solicitada,
                    'negocio': negocio_instancia 
                }
            )

            if not creado:
                item_carrito.cantidad += cantidad_solicitada
                item_carrito.save()
            
            respuesta_serializer = ItemCarritoSerializer(item_carrito)
            return Response(respuesta_serializer.data, status=status.HTTP_201_CREATED if creado else status.HTTP_200_OK)
        
        else: 
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerCarritoAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
            serializer = CarritoSerializer(carrito, context={'request': request}) # Pasar contexto
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print("----------------------------------------------------")
            print(f"ERROR EN VerCarritoAPIView (se devolvera carrito por defecto): {type(e).__name__} - {str(e)}")
            traceback.print_exc() 
            print("----------------------------------------------------")
            default_carrito_data = {
                "id": None, "usuario": request.user.id if request.user and request.user.is_authenticated else None,
                "items": [], "creado_en": None, "actualizado_en": None, "total_carrito": "0.00" 
            }
            return Response(default_carrito_data, status=status.HTTP_200_OK)


class ItemCarritoViewSet(viewsets.ModelViewSet):
    serializer_class = ItemCarritoSerializer 
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated:
            try:
                carrito = Carrito.objects.get(usuario=self.request.user)
                return ItemCarrito.objects.filter(carrito=carrito).select_related('producto', 'negocio')
            except Carrito.DoesNotExist:
                return ItemCarrito.objects.none()
        return ItemCarrito.objects.none()

    def partial_update(self, request, *args, **kwargs):
        item = self.get_object() 
        cantidad_nueva = request.data.get('cantidad')
        if cantidad_nueva is None:
            return Response({"error": "El campo 'cantidad' es requerido."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cantidad_nueva = int(cantidad_nueva)
            if cantidad_nueva <= 0:
                # Si la cantidad es 0, eliminar el item
                if cantidad_nueva == 0:
                    item.delete()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                return Response({"error": "La cantidad debe ser mayor o igual a cero."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "La cantidad debe ser un numero entero."}, status=status.HTTP_400_BAD_REQUEST)
        
        item.cantidad = cantidad_nueva
        item.save(update_fields=['cantidad']) 
        
        if not item.precio_al_agregar and item.producto: # Esto deberia haberse establecido al crear
            item.precio_al_agregar = item.producto.precio
            item.save(update_fields=['precio_al_agregar'])

        serializer = self.get_serializer(item, context={'request': request}) # Pasar contexto
        return Response(serializer.data)

class StockInsuficienteError(APIException): # Clase de excepción personalizada
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Stock insuficiente para uno o mas productos.'
    default_code = 'stock_insufficient'

class CrearPedidoAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            carrito = get_object_or_404(Carrito, usuario=request.user)
            items_carrito = carrito.items.all().select_related('producto', 'negocio') # Optimizar consulta
            if not items_carrito.exists():
                return Response({"error": "Tu carrito esta vacio."}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Validar stock antes de crear el pedido
                for item_c_val in items_carrito:
                    prod_val = item_c_val.producto
                    if prod_val is None:
                        # Este caso debería manejarse de forma más robusta, quizás eliminando items con productos nulos del carrito
                        return Response({"error": f"Un producto en tu carrito (ID original: {item_c_val.producto_id if hasattr(item_c_val, 'producto_id') else 'desconocido'}) ya no esta disponible."}, status=status.HTTP_400_BAD_REQUEST)
                    if prod_val.stock < item_c_val.cantidad:
                        # Devolver una respuesta 400 directamente con el mensaje de error específico
                        raise StockInsuficienteError(detail=f"Stock insuficiente para el producto: {prod_val.nombre}. Disponible: {prod_val.stock}, Solicitado: {item_c_val.cantidad}")

                pedido = Pedido.objects.create(usuario=request.user)
                total_pedido_calculado = 0
                
                for item_c in items_carrito:
                    prod = item_c.producto
                    # La validación de stock ya se hizo arriba, pero una doble verificación no está de más
                    # o se podría asumir que el stock es suficiente si se pasó la validación anterior.
                    # Aquí procedemos directamente a descontar.
                    
                    ItemPedido.objects.create(
                        pedido=pedido, 
                        producto=prod, 
                        negocio=item_c.negocio, 
                        nombre_producto=prod.nombre,
                        precio_unitario_pedido=item_c.precio_al_agregar or prod.precio,
                        cantidad=item_c.cantidad
                        # subtotal_pedido se calcula automaticamente en ItemPedido.save()
                    )
                    
                    prod.stock -= item_c.cantidad
                    prod.save(update_fields=['stock'])
                    
                    precio_item = item_c.precio_al_agregar or prod.precio
                    total_pedido_calculado += precio_item * item_c.cantidad
                
                pedido.total_pedido = total_pedido_calculado
                pedido.save(update_fields=['total_pedido'])
                
                carrito.items.all().delete() # Limpiar el carrito
                
            serializer = PedidoSerializer(pedido, context={'request': request}) # Pasar contexto
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Carrito.DoesNotExist:
            return Response({"error": "No se encontro un carrito para este usuario."}, status=status.HTTP_404_NOT_FOUND)
        except Producto.DoesNotExist: 
            return Response({"error": "Uno de los productos en el carrito ya no existe."}, status=status.HTTP_400_BAD_REQUEST)
        except StockInsuficienteError as e: # Capturar la excepción personalizada
            return Response({"error": str(e.detail)}, status=e.status_code)
        except Exception as e: # Capturar otras excepciones inesperadas
            traceback.print_exc()
            # Para errores inesperados, sí es apropiado un 500
            return Response({"error": "Ocurrio un error inesperado en el servidor al procesar el pedido."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MisPedidosAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        print(f"--- DEBUG: MisPedidosAPIView.get() para usuario: {request.user} ---")
        pedidos = Pedido.objects.filter(usuario=request.user).prefetch_related(
            'items_pedido__producto__negocio', # Optimizar consultas
            'items_pedido__negocio'
        ).order_by('-creado_en')
        
        for p in pedidos:
            print(f"--- DEBUG: Pedido ID {p.id} - Estado desde BD: {p.estado} ---")
            
        serializer = PedidoSerializer(pedidos, many=True, context={'request': request}) # Pasar contexto
        return Response(serializer.data, status=status.HTTP_200_OK)

class GestionPedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer 
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options'] 

    def get_queryset(self):
        user = self.request.user
        if not (user.is_authenticated and hasattr(user, 'rol') and user.rol == 'negocio'):
            raise PermissionDenied("No tienes permiso para gestionar pedidos de negocios.")
        
        negocios_del_usuario = Negocio.objects.filter(usuario=user)
        if not negocios_del_usuario.exists():
            return Pedido.objects.none()
        
        return Pedido.objects.filter(
            items_pedido__negocio__in=negocios_del_usuario
        ).exclude( # Opcional: excluir pedidos que el dueño se hizo a si mismo
            # usuario=user 
        ).distinct().order_by('-creado_en').prefetch_related(
            'items_pedido__producto', 
            'items_pedido__negocio',
            'usuario' # Para el ClientePedidoSerializer
        )

    def partial_update(self, request, *args, **kwargs):
        pedido = self.get_object() 
        nuevo_estado = request.data.get('estado')
        if not nuevo_estado:
            return Response({"error": "El campo 'estado' es requerido para la actualizacion."}, status=status.HTTP_400_BAD_REQUEST)
        
        estado_choices_validos = [choice[0] for choice in Pedido.ESTADO_CHOICES]
        if nuevo_estado.upper() not in estado_choices_validos:
            return Response({"error": f"Estado '{nuevo_estado}' no es valido. Validos son: {', '.join(estado_choices_validos)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        pedido.estado = nuevo_estado.upper()
        pedido.save(update_fields=['estado'])
        
        serializer = self.get_serializer(pedido, context={'request': request}) # Pasar contexto
        return Response(serializer.data)