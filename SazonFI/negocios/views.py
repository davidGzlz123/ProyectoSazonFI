# negocios/views.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from .models import Negocio
from productos.models import Producto
from .serializers import NegocioSerializer
from productos.serializers import ProductoSerializer

User = get_user_model() # Esto obtendra tu modelo de Usuario (sea el default o uno personalizado)

class NegocioViewSet(viewsets.ModelViewSet):
    serializer_class = NegocioSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication] 
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] 

    def get_queryset(self):
        user = self.request.user
        action = self.action
        
        # Intenta obtener el rol de forma segura.
        # Si tu campo de rol se llama diferente (ej. 'tipo_usuario'), cambialo aqui.
        user_rol_value = getattr(user, 'rol', 'ROL_NO_DEFINIDO_EN_USUARIO') 

        print(f"--- DEBUG: NegocioViewSet.get_queryset() ---")
        print(f"--- Action: {action}")
        print(f"--- User: {user}")
        print(f"--- Authenticated: {user.is_authenticated}")
        print(f"--- Valor del atributo 'rol' del usuario: '{user_rol_value}'") 
        print(f"-------------------------------------------")


        if action == 'list': # Esto es para GET /api/negocios/
            # ----- ESTA ES LA CONDICION CRUCIAL -----
            # Asegurate de que 'user.rol' sea el nombre correcto del atributo en tu modelo User
            # y que 'negocio' sea el valor exacto para los usuarios de tipo negocio.
            if user.is_authenticated and hasattr(user, 'rol') and user.rol == 'negocio':
                print(f"--- NegocioViewSet.get_queryset() [LISTA PARA DUENO DE NEGOCIO] - Usuario: {user.username}, Rol: {user_rol_value} - Filtrando por sus negocios.")
                return Negocio.objects.filter(usuario=user)
            else:
                # Para la lista publica (cliente.html, index.html, o usuarios no autenticados/no-negocio)
                print(f"--- NegocioViewSet.get_queryset() [LISTA PUBLICA] - Usuario: {user.username if user.is_authenticated else 'Anonimo'}, Rol: {user_rol_value} - Devolviendo todos los negocios.")
                return Negocio.objects.all() 
        elif user.is_authenticated:
            # Para acciones de detalle (retrieve, update, delete)
            print(f"--- NegocioViewSet.get_queryset() [DETALLE/ESCRITURA] - Usuario: {user.username} - Filtrando por sus negocios.")
            return Negocio.objects.filter(usuario=user)
        
        print(f"--- NegocioViewSet.get_queryset() - Fallback (ej. no autenticado para accion no-lista) - Devolviendo queryset vacio.")
        return Negocio.objects.none()

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object() 
        if instance.usuario != self.request.user:
            raise PermissionDenied("No tienes permiso para actualizar este negocio.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.usuario != self.request.user: 
            raise PermissionDenied("No tienes permiso para eliminar este negocio.")
        instance.delete()



class ProductoViewSet(viewsets.ModelViewSet): # ANIDADO
    serializer_class = ProductoSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication] 
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        negocio_pk = self.kwargs.get('negocio_pk') 
        if not negocio_pk:
            return Producto.objects.none()
        try:
            negocio = Negocio.objects.get(pk=negocio_pk)
        except Negocio.DoesNotExist:
            return Producto.objects.none() 
        return Producto.objects.filter(negocio=negocio)

    def create(self, request, *args, **kwargs):
        negocio_pk_from_url = kwargs.get('negocio_pk')
        try:
            Negocio.objects.get(pk=negocio_pk_from_url, usuario=request.user)
        except Negocio.DoesNotExist:
            raise PermissionDenied("No tienes permiso para agregar productos a este negocio o el negocio no existe.")
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        negocio_pk = self.kwargs.get('negocio_pk') 
        try:
            negocio = Negocio.objects.get(pk=negocio_pk, usuario=self.request.user) 
        except Negocio.DoesNotExist:
            raise PermissionDenied("No tienes permiso para agregar productos a este negocio o el negocio no existe.")
        serializer.save(negocio=negocio) 

    def perform_update(self, serializer):
        producto = self.get_object()
        if producto.negocio.usuario != self.request.user:
             raise PermissionDenied("No tienes permiso para editar este producto.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.negocio.usuario != self.request.user:
             raise PermissionDenied("No tienes permiso para eliminar este producto.")
        instance.delete()

# Vista HTML
# Asegurate de que esta definicion de funcion este completa y correcta:
def vista_html_productos_por_negocio(request, id_negocio):
    negocio = get_object_or_404(Negocio, pk=id_negocio)
    lista_productos = Producto.objects.filter(negocio=negocio)
    context = {
        'negocio': negocio,
        'nombre_negocio': negocio.nombre,
        'id_negocio_para_js': id_negocio,
        'productos_list': lista_productos, 
    }
    return render(request, 'negocio/productos_negocio.html', context)
