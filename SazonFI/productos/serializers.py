# productos/serializers.py
from rest_framework import serializers
from .models import Producto
# from negocios.serializers import NegocioSerializer # Solo si necesitas anidar el NegocioSerializer completo

class ProductoSerializer(serializers.ModelSerializer):
    negocio = serializers.PrimaryKeyRelatedField(read_only=True) 
    
    imagen = serializers.ImageField(required=False, allow_null=True, use_url=False, max_length=None)
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id', 
            'nombre', 
            'descripcion', 
            'precio', 
            'stock', 
            'imagen',    # Para la subida
            'imagen_url',# Para la lectura
            'categoria',   
            'negocio',
            # Anade 'creado_en', 'actualizado_en' si existen en tu modelo Producto
            # 'creado_en', 
            # 'actualizado_en'
        ]
        # Si tienes 'creado_en', 'actualizado_en', anadelos a read_only_fields si no lo estan ya
        read_only_fields = ('negocio', 'imagen_url') # Anade 'creado_en', 'actualizado_en' si aplica

    def get_imagen_url(self, obj):
        request = self.context.get('request')
        imagen_model_url = obj.get_imagen_url() # Llama al metodo del modelo
        
        if request and imagen_model_url and not imagen_model_url.startswith(('http://', 'https://')):
            return request.build_absolute_uri(imagen_model_url)
        return imagen_model_url
