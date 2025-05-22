# negocios/models.py
from django.db import models
from django.conf import settings 

DEFAULT_LOGO_URL = 'https://placehold.co/300x200/EFEFEF/AAAAAA?text=Sin+Logo'

class Negocio(models.Model):
    CATEGORIAS = (
        ('franquicia', 'Franquicia'),
        ('estudiante', 'Estudiante'),
    )

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='franquicia', blank=True, null=True, help_text="Categoría del negocio")
    logo = models.ImageField(upload_to='negocios/logos/', null=True, blank=True)
    # Los campos creado_en y actualizado_en han sido eliminados segun el requerimiento

    def __str__(self):
        return self.nombre

    def get_logo_url(self):
        if self.logo and hasattr(self.logo, 'url'):
            return self.logo.url
        return DEFAULT_LOGO_URL
