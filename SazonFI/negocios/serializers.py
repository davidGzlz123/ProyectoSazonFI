# negocios/serializers.py
from rest_framework import serializers
from .models import Negocio # Asegúrate que Negocio se importe desde los modelos de esta app

class NegocioSerializer(serializers.ModelSerializer):
    # Para la subida (write), DRF manejara el archivo.
    # 'required=False' permite que el campo no se envie al actualizar si no se cambia la imagen.
    logo = serializers.ImageField(required=False, allow_null=True, use_url=False, max_length=None) 
    
    # Para la lectura (GET), expondremos la URL completa del logo.
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Negocio
        # Asegurarse de que 'creado_en' y 'actualizado_en' NO esten aqui,
        # ya que fueron eliminados del modelo Negocio.
        fields = [
            'id', 
            'usuario', 
            'nombre', 
            'descripcion', 
            'direccion', 
            'telefono', 
            'logo', # Para la subida
            'logo_url' # Para la lectura
        ]
        # 'usuario' y 'logo_url' son de solo lectura por su definicion o por ser SerializerMethodField.
        # No es necesario 'creado_en' ni 'actualizado_en' en read_only_fields si no estan en 'fields'.
        read_only_fields = ('usuario', 'logo_url') 

    def get_logo_url(self, obj):
        request = self.context.get('request')
        # Llama al metodo del modelo que ya tiene la logica de la URL por defecto
        logo_model_url = obj.get_logo_url() 
        
        if request and logo_model_url and not logo_model_url.startswith(('http://', 'https://')):
            # Si es una ruta relativa (ej. /media/...) y tenemos request, la hacemos absoluta
            return request.build_absolute_uri(logo_model_url)
        return logo_model_url # Devuelve la URL absoluta o la URL placeholder

    # to_internal_value se usa para modificar datos antes de la validacion/deserializacion.
    # En este caso, la implementacion por defecto de super() es suficiente.
    def to_internal_value(self, data):
        return super().to_internal_value(data)
