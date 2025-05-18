# api/urls.py
from django.urls import path, include
from rest_framework import routers
from rest_framework_nested import routers as nested_routers

from .views import RegistroUsuarioViewSet, InicioSesionAPIView 
from negocios.views import NegocioViewSet
from productos.views import ProductoViewSet as MainProductoViewSet 
from negocios.views import ProductoViewSet as NegociosProductoViewSet 

from carritos.views import (
    AgregarItemCarritoAPIView, 
    VerCarritoAPIView,
    CrearPedidoAPIView,
    ItemCarritoViewSet,
    MisPedidosAPIView,
    GestionPedidoViewSet 
)

router = routers.DefaultRouter()
router.register(r'registro', RegistroUsuarioViewSet, basename='registro-api')
router.register(r'negocios', NegocioViewSet, basename='negocios-api') 
router.register(r'productos', MainProductoViewSet, basename='main-productos-api')
router.register(r'carrito-items', ItemCarritoViewSet, basename='carrito-item')
router.register(r'gestion-pedidos', GestionPedidoViewSet, basename='gestion-pedido')

negocios_api_router = nested_routers.NestedDefaultRouter(router, r'negocios', lookup='negocio') 
negocios_api_router.register(
    r'productos', 
    NegociosProductoViewSet, 
    basename='negocio-productos' 
)
# La accion personalizada 'pedidos_recibidos' en NegocioViewSet se accede via:
# GET /api/negocios/<negocio_pk>/pedidos-recibidos/
# No necesita una entrada separada en urlpatterns si esta registrada con el router anidado
# o con el router principal (a traves de NegocioViewSet).
# Como es una @action en NegocioViewSet, el router.register(r'negocios', NegocioViewSet)
# y el negocios_api_router ya la hacen accesible.

urlpatterns = [
    path('', include(router.urls)), 
    path('', include(negocios_api_router.urls)), # Esto es importante para las rutas anidadas
    
    path('login/', InicioSesionAPIView.as_view(), name='api-login'),

    path('carrito/agregar/', AgregarItemCarritoAPIView.as_view(), name='api_carrito_agregar_item'),
    path('carrito/', VerCarritoAPIView.as_view(), name='api_ver_carrito'), 
    path('pedidos/crear/', CrearPedidoAPIView.as_view(), name='api_crear_pedido'),
    path('pedidos/mis-pedidos/', MisPedidosAPIView.as_view(), name='api_mis_pedidos'),
]
