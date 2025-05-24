# SazonFI/usuarios/serializers.py
from rest_framework import serializers
from .models import Usuario # Asegurate que Usuario se importe desde tus modelos

class UsuarioSerializer(serializers.ModelSerializer):
    # Hacemos 'password' de solo escritura y requerido para el registro.
    # El style={'input_type': 'password'} ayuda a que DRF lo represente adecuadamente en la API explorable.
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    # Es buena practica asegurar que el email tambien sea requerido en el serializador
    # si lo es en el modelo y fundamental para tu logica (ej. confirmacion de cuenta).
    # Tu modelo Usuario lo tiene como blank=True, asi que required=False es mas consistente aqui
    # a menos que quieras forzarlo en el registro API.
    # Si tu frontend siempre envia el email durante el registro, required=True esta bien.
    email = serializers.EmailField(required=True) # Asumiendo que el frontend siempre lo envia para registro

    class Meta:
        model = Usuario
        # Incluimos 'password' en los fields para que el serializador lo reciba durante la creacion.
        # 'first_name' y 'last_name' son opcionales (blank=True en el modelo AbstractUser).
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'rol']
        read_only_fields = ['id'] # El ID es de solo lectura y se genera automaticamente.
        # 'rol' se espera que se envie durante la creacion desde el frontend.

    def create(self, validated_data):
        """
        Sobrescribimos el metodo create para usar el metodo create_user de Django,
        que se encarga de hashear la contrasena correctamente.
        """
        # Se utiliza .get() para campos que podrian no venir en validated_data si no son requeridos
        # o si tienen un valor por defecto en el modelo que se quiera respetar, aunque aqui
        # username, email y password son manejados como requeridos por create_user.
        user = Usuario.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'], # create_user se encarga de hashear esta contrasena
            first_name=validated_data.get('first_name', ''), # Proporciona un default si no viene
            last_name=validated_data.get('last_name', ''),   # Proporciona un default si no viene
            rol=validated_data.get('rol', 'cliente') # Asigna rol, con 'cliente' como default si no se provee
        )
        return user

    def update(self, instance, validated_data):
        """
        Maneja la actualizacion de una instancia de Usuario.
        Si se proporciona una nueva contrasena, se hashea.
        """
        # Actualiza los campos estandar
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.rol = validated_data.get('rol', instance.rol)

        # Manejo especial para la contrasena
        password = validated_data.get('password', None)
        if password:
            instance.set_password(password) # Usa set_password para hashear la nueva contrasena
        
        instance.save()
        return instance