# negocios/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
import traceback

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from .models import Negocio
from productos.models import Producto
from .serializers import NegocioSerializer
from productos.serializers import ProductoSerializer

from carritos.models import ItemPedido 
from carritos.serializers import ItemPedidoSerializer 

from django.db.models import Q

User = get_user_model()

class NegocioViewSet(viewsets.ModelViewSet):
    serializer_class = NegocioSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication] 
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] 

    def get_queryset(self):
        user = self.request.user
        action = self.action
        user_rol_value = getattr(user, 'rol', 'ROL_NO_DEFINIDO_EN_USUARIO')

        query = self.request.GET.get('q', '').strip()
        categoria = self.request.GET.get('categoria', '').lower()
        orden = self.request.GET.get('orden', '').lower()

        print(f"--- DEBUG: NegocioViewSet.get_queryset() --- Action: {action}, User: {user}, Authenticated: {user.is_authenticated}, Rol: '{user_rol_value}', Query: '{query}', Categoria: '{categoria}', Orden: '{orden}'")

        if action == 'list':
            if user.is_authenticated and hasattr(user, 'rol') and user.rol == 'negocio':
                queryset = Negocio.objects.filter(usuario=user)
                if query:
                    queryset = queryset.filter(
                        Q(nombre__icontains=query) |
                        Q(descripcion__icontains=query) |
                        Q(direccion__icontains=query) |
                        Q(producto__nombre__icontains=query)
                    ).distinct()
            else:
                queryset = Negocio.objects.all()
                if query:
                    queryset = queryset.filter(
                        Q(nombre__icontains=query) |
                        Q(descripcion__icontains=query) |
                        Q(direccion__icontains=query) |
                        Q(producto__nombre__icontains=query)
                    ).distinct()

            # Filtrado por categoría si es válida
            if categoria in ['franquicia', 'estudiante']:
                queryset = queryset.filter(categoria=categoria)

            # Ordenamiento si se indica
            if orden == 'alfabetico':
                queryset = queryset.order_by('nombre')

            print(f"--- Lista filtrada y ordenada: {queryset.count()} negocios ---")
            return queryset

        elif user.is_authenticated:
            queryset = Negocio.objects.filter(usuario=user)
            if query:
                queryset = queryset.filter(
                    Q(nombre__icontains=query) |
                    Q(descripcion__icontains=query) |
                    Q(direccion__icontains=query) |
                    Q(producto__nombre__icontains=query)
                ).distinct()
            print(f"--- Detalle/Escritura, filtrados: {queryset.count()} ---")
            return queryset

        print(f"--- Fallback, queryset vacio ---")
        return Negocio.objects.none()


    def perform_create(self, serializer): serializer.save(usuario=self.request.user)
    def perform_update(self, serializer):
        instance = self.get_object() 
        if instance.usuario != self.request.user: raise PermissionDenied("No tienes permiso para actualizar este negocio.")
        serializer.save()
    def perform_destroy(self, instance):
        if instance.usuario != self.request.user: raise PermissionDenied("No tienes permiso para eliminar este negocio.")
        instance.delete()
    
    @action(detail=True, methods=['get'], url_path='pedidos-recibidos', permission_classes=[permissions.IsAuthenticated])
    def pedidos_recibidos(self, request, pk=None): 
        print(f"--- DEBUG: NegocioViewSet.pedidos_recibidos() - Solicitud para Negocio PK: {pk} por Usuario: {request.user} ---")
        try:
            negocio = self.get_object() 
            print(f"--- DEBUG: NegocioViewSet.pedidos_recibidos() - Negocio obtenido: {negocio.nombre} ---")
            
            items_del_negocio_en_pedidos = ItemPedido.objects.filter(negocio=negocio).select_related(
                'pedido', 'pedido__usuario', 'producto', 'negocio' 
            ).order_by('-pedido__creado_en', 'id')
            print(f"--- DEBUG: NegocioViewSet.pedidos_recibidos() - Items encontrados: {items_del_negocio_en_pedidos.count()} ---")

            page = self.paginate_queryset(items_del_negocio_en_pedidos)
            if page is not None:
                serializer = ItemPedidoSerializer(page, many=True, context={'request': request})
                print("--- DEBUG: NegocioViewSet.pedidos_recibidos() - Serializando pagina de items ---")
                return self.get_paginated_response(serializer.data)

            serializer = ItemPedidoSerializer(items_del_negocio_en_pedidos, many=True, context={'request': request})
            print("--- DEBUG: NegocioViewSet.pedidos_recibidos() - Serializando todos los items ---")
            return Response(serializer.data)
        except PermissionDenied as e: 
            print(f"--- PERMISSION DENIED en pedidos_recibidos para negocio {pk} y usuario {request.user}: {str(e)} ---")
            return Response({"error": "No tienes permiso para acceder a estos pedidos."}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            print("----------------------------------------------------")
            print(f"ERROR EN NegocioViewSet.pedidos_recibidos: {type(e).__name__} - {str(e)}")
            traceback.print_exc()
            print("----------------------------------------------------")
            return Response(
                {"error": "Ocurrio un error al obtener los pedidos recibidos.", "detalle_servidor": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProductoViewSet(viewsets.ModelViewSet): # ANIDADO
    serializer_class = ProductoSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication] 
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']
    def get_queryset(self):
        negocio_pk = self.kwargs.get('negocio_pk') 
        if not negocio_pk: return Producto.objects.none()
        try: negocio = Negocio.objects.get(pk=negocio_pk)
        except Negocio.DoesNotExist: return Producto.objects.none() 
        return Producto.objects.filter(negocio=negocio)
    def create(self, request, *args, **kwargs):
        negocio_pk_from_url = kwargs.get('negocio_pk')
        try: Negocio.objects.get(pk=negocio_pk_from_url, usuario=request.user)
        except Negocio.DoesNotExist: raise PermissionDenied("No tienes permiso para agregar productos a este negocio o el negocio no existe.")
        return super().create(request, *args, **kwargs)
    def perform_create(self, serializer):
        negocio_pk = self.kwargs.get('negocio_pk') 
        try: negocio = Negocio.objects.get(pk=negocio_pk, usuario=self.request.user) 
        except Negocio.DoesNotExist: raise PermissionDenied("No tienes permiso para agregar productos a este negocio o el negocio no existe.")
        serializer.save(negocio=negocio) 
    def perform_update(self, serializer):
        producto = self.get_object()
        if producto.negocio.usuario != self.request.user: raise PermissionDenied("No tienes permiso para editar este producto.")
        serializer.save()
    def perform_destroy(self, instance):
        if instance.negocio.usuario != self.request.user: raise PermissionDenied("No tienes permiso para eliminar este producto.")
        instance.delete()

def vista_html_productos_por_negocio(request, id_negocio):
    negocio = get_object_or_404(Negocio, pk=id_negocio)
    lista_productos = Producto.objects.filter(negocio=negocio)
    context = { 'negocio': negocio, 'nombre_negocio': negocio.nombre, 'id_negocio_para_js': id_negocio, 'productos_list': lista_productos, }
    return render(request, 'negocio/productos_negocio.html', context)
