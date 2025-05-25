from rest_framework import serializers
from .models import Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'rol']
        # 'password' se excluye por seguridad; se manejar� de otra manera
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        return Usuario.objects.create_user(**validated_data)