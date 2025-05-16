# productos/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied # Para errores de permiso
from .models import Producto
from .serializers import ProductoSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal para manejar productos.
    Permite listar (con filtro opcional por negocio), recuperar, actualizar y eliminar productos.
    Las operaciones de actualizacion y eliminacion requieren que el usuario sea el propietario
    del negocio al que pertenece el producto.
    """
    serializer_class = ProductoSerializer
    # Es importante definir los authentication_classes aqui tambien si no estan globalmente
    # from rest_framework.authentication import TokenAuthentication, SessionAuthentication
    # authentication_classes = [TokenAuthentication, SessionAuthentication] 
    permission_classes = [permissions.IsAuthenticated] # Solo usuarios autenticados pueden interactuar

    # Queryset base para todas las acciones. get_object() usara este.
    queryset = Producto.objects.all()

    def get_queryset(self):
        """
        Este metodo se usa principalmente para la accion 'list' (GET /api/productos/).
        Para otras acciones (retrieve, update, delete), get_object() usara el self.queryset definido a nivel de clase.
        """
        # Obtener el queryset base (Producto.objects.all())
        queryset = super().get_queryset()

        # Si la accion es 'list', podemos aplicar filtros adicionales.
        if self.action == 'list':
            negocio_id = self.request.query_params.get('negocio')
            if negocio_id:
                # Filtrar por negocio si se proporciona el parametro
                queryset = queryset.filter(negocio_id=negocio_id)
                # Adicionalmente, podrias querer asegurar que solo se listen productos
                # de negocios del usuario actual, incluso si se especifica un negocio_id.
                # queryset = queryset.filter(negocio__usuario=self.request.user)
            else:
                # Si no se especifica un negocio_id para la lista,
                # decidir que devolver. Podria ser una lista vacia,
                # o productos de todos los negocios del usuario, o nada.
                # Devolver una lista vacia es mas seguro si no se quiere exponer todo.
                # O, si quieres listar todos los productos de los negocios del usuario:
                # queryset = queryset.filter(negocio__usuario=self.request.user)
                # Por ahora, si no hay filtro, devolvemos una lista vacia para /api/productos/
                return Producto.objects.none() 
        
        # Para acciones de detalle (retrieve, update, partial_update, destroy),
        # DRF usara el queryset definido a nivel de clase (Producto.objects.all())
        # para buscar el objeto por PK. Los permisos se aplican despues.
        return queryset

    def perform_update(self, serializer):
        """
        Asegura que solo el propietario del negocio pueda actualizar el producto.
        """
        producto = serializer.instance # El producto ya fue obtenido por get_object()
        if producto.negocio.usuario != self.request.user:
            raise PermissionDenied("No tienes permiso para editar este producto.")
        serializer.save()

    def perform_destroy(self, instance):
        """
        Asegura que solo el propietario del negocio pueda eliminar el producto.
        """
        # 'instance' es el producto obtenido por get_object()
        if instance.negocio.usuario != self.request.user:
            raise PermissionDenied("No tienes permiso para eliminar este producto.")
        instance.delete()
