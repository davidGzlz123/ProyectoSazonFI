# productos/models.py
from django.db import models
from negocios.models import Negocio 

DEFAULT_PRODUCTO_IMAGEN_URL = 'https://placehold.co/300x200/EFEFEF/AAAAAA?text=Sin+Imagen'

class Producto(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True) # Permitir null
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    categoria = models.CharField(max_length=100, blank=True, null=True)
    # Si tenias creado_en y actualizado_en, mantenlos o anadelos:
    # creado_en = models.DateTimeField(auto_now_add=True, null=True, blank=True) # null y blank si son nuevas
    # actualizado_en = models.DateTimeField(auto_now=True, null=True, blank=True)


    def __str__(self):
        return self.nombre

    def get_imagen_url(self):
        if self.imagen and hasattr(self.imagen, 'url'):
            return self.imagen.url
        return DEFAULT_PRODUCTO_IMAGEN_URL
