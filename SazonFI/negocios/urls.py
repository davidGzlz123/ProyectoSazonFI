# negocios/urls.py
from django.urls import path
from . import views  # Importa tus vistas de la app 'negocios', incluida la nueva vista_html_productos_por_negocio

app_name = 'negocios' # Es una buena práctica para organizar las URLs de las plantillas

urlpatterns = [
    # URL para la página HTML que muestra los productos de un negocio específico
    path('<int:id_negocio>/productos/', views.vista_html_productos_por_negocio, name='pagina_productos_de_negocio'),

    # Aquí podrías añadir otras URLs que sirvan páginas HTML para la app 'negocios'.
    # Por ejemplo, si un dueño de negocio tiene un panel:
    # path('dashboard/', views.dashboard_negocio, name='dashboard_negocio'),
]