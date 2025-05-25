# SazonFI/SazonFI/urls.py (Archivo principal de URLs de tu proyecto)
from django.contrib import admin
from django.urls import path, include # Asegurate de que 'include' este importado
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('accounts/', include('allauth.urls')), # URLs para autenticacion de allauth

    path('admin/', admin.site.urls),

    # --- INCLUSION DE LAS URLs DE TU API ---
    path('api/', include('api.urls')), # �ESTA LINEA ES CRUCIAL!

    # URLs para Paginas HTML de la Aplicacion 'negocios'
    path('negocios/', include('negocios.urls')), 

    # URLs para Paginas HTML de la Aplicacion 'carritos'
    path('carrito/', include('carritos.urls')), # Para la pagina /carrito/ que muestra el HTML

    # URLs para Paginas HTML Generales del Sitio
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('login/', TemplateView.as_view(template_name='usuarios/login.html'), name='login'),
    path('registro/', TemplateView.as_view(template_name='usuarios/registro.html'), name='registro'),
    path('negocio/', TemplateView.as_view(template_name='negocio/negocio.html'), name='pagina_negocio'), 
    path('cliente/', TemplateView.as_view(template_name='cliente/cliente.html'), name='lista_negocios_cliente'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)