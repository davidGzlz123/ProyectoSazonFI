# api/urls.py
from django.urls import path, include
from rest_framework import routers
from rest_framework_nested import routers as nested_routers

# Vistas para endpoints de API existentes
from .views import RegistroUsuarioViewSet, InicioSesionAPIView 
from negocios.views import NegocioViewSet
from productos.views import ProductoViewSet as MainProductoViewSet 
from negocios.views import ProductoViewSet as NegociosProductoViewSet 

# --- IMPORTACIONES CLAVE PARA EL CARRITO Y PEDIDOS ---
from carritos.views import (
    AgregarItemCarritoAPIView, 
    VerCarritoAPIView,
    CrearPedidoAPIView,
    ItemCarritoViewSet # <--- NUEVA IMPORTACION
)

# Router principal
router = routers.DefaultRouter()
router.register(r'registro', RegistroUsuarioViewSet, basename='registro-api')
router.register(r'negocios', NegocioViewSet, basename='negocios-api') 
router.register(r'productos', MainProductoViewSet, basename='main-productos-api')

# --- NUEVO ROUTER PARA ITEMS DEL CARRITO ---
# Esto creara URLs como /api/carrito-items/ y /api/carrito-items/<pk>/
router.register(r'carrito-items', ItemCarritoViewSet, basename='carrito-item')


# Router anidado para productos dentro de negocios
negocios_api_router = nested_routers.NestedDefaultRouter(router, r'negocios', lookup='negocio') 
negocios_api_router.register(
    r'productos', 
    NegociosProductoViewSet, 
    basename='negocio-productos' 
)

urlpatterns = [
    path('', include(router.urls)), # Incluye las rutas del router principal (incluido carrito-items)
    path('', include(negocios_api_router.urls)), 
    
    path('login/', InicioSesionAPIView.as_view(), name='api-login'),

    # URLs de carrito y pedidos (las vistas APIView especificas)
    path('carrito/agregar/', AgregarItemCarritoAPIView.as_view(), name='api_carrito_agregar_item'),
    path('carrito/', VerCarritoAPIView.as_view(), name='api_ver_carrito'), 
    path('pedidos/crear/', CrearPedidoAPIView.as_view(), name='api_crear_pedido'),
]
