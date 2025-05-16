# carritos/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction 
import traceback 

from rest_framework import viewsets, permissions, status # Importar viewsets
from rest_framework.views import APIView
from rest_framework.response import Response


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
            serializer = CarritoSerializer(carrito)
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


# --- VIEWSET PARA MANEJAR ITEMS INDIVIDUALES DEL CARRITO (ACTUALIZAR CANTIDAD, ELIMINAR) ---
class ItemCarritoViewSet(viewsets.ModelViewSet):
    serializer_class = ItemCarritoSerializer 
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options'] # Solo permitir estos metodos

    def get_queryset(self):
        # El usuario solo puede ver/modificar items de su propio carrito
        if self.request.user and self.request.user.is_authenticated:
            try:
                carrito = Carrito.objects.get(usuario=self.request.user)
                return ItemCarrito.objects.filter(carrito=carrito)
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
                return Response({"error": "La cantidad debe ser mayor a cero."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "La cantidad debe ser un numero entero."}, status=status.HTTP_400_BAD_REQUEST)

        item.cantidad = cantidad_nueva
        item.save(update_fields=['cantidad']) 
        
        if not item.precio_al_agregar and item.producto:
            item.precio_al_agregar = item.producto.precio
            item.save(update_fields=['precio_al_agregar'])

        serializer = self.get_serializer(item)
        return Response(serializer.data)

class CrearPedidoAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, *args, **kwargs):
        try:
            carrito = get_object_or_404(Carrito, usuario=request.user)
            items_carrito = carrito.items.all()

            if not items_carrito.exists():
                return Response({"error": "Tu carrito esta vacio."}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                pedido = Pedido.objects.create(usuario=request.user)
                total_pedido_calculado = 0
                for item_carrito in items_carrito:
                    producto_actual = item_carrito.producto
                    if producto_actual.stock < item_carrito.cantidad:
                        raise Exception(f"No hay suficiente stock para: {producto_actual.nombre}. Disponible: {producto_actual.stock}, Solicitado: {item_carrito.cantidad}")
                    ItemPedido.objects.create(
                        pedido=pedido, producto=producto_actual, negocio=item_carrito.negocio, 
                        nombre_producto=producto_actual.nombre,
                        precio_unitario_pedido=item_carrito.precio_al_agregar or producto_actual.precio,
                        cantidad=item_carrito.cantidad
                    )
                    producto_actual.stock -= item_carrito.cantidad
                    producto_actual.save(update_fields=['stock'])
                    total_pedido_calculado += (item_carrito.precio_al_agregar or producto_actual.precio) * item_carrito.cantidad
                pedido.total_pedido = total_pedido_calculado
                pedido.save(update_fields=['total_pedido'])
                carrito.items.all().delete()
            serializer = PedidoSerializer(pedido)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Carrito.DoesNotExist:
            return Response({"error": "No se encontro un carrito para este usuario."}, status=status.HTTP_404_NOT_FOUND)
        except Producto.DoesNotExist:
            return Response({"error": "Uno de los productos en el carrito ya no existe."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("----------------------------------------------------")
            print(f"ERROR EN CrearPedidoAPIView: {type(e).__name__} - {str(e)}")
            traceback.print_exc()
            print("----------------------------------------------------")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
