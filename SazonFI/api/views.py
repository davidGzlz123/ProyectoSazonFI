from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from usuarios.models import Usuario
from usuarios.serializers import UsuarioSerializer
from rest_framework.views import APIView

class RegistroUsuarioViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        serializer = UsuarioSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.save()
            usuario.set_password(request.data['password'])
            usuario.save()
            return Response({'message': 'Usuario registrado con exito'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InicioSesionAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            #  ¡CORRECCIÓN IMPORTANTE!  Asegúrate de que 'rol' existe en tu modelo Usuario
            rol = user.rol if hasattr(user, 'rol') else 'usuario' 
            return Response({
                'token': token.key,
                'rol': rol 
            })
        return Response({'error': 'Credenciales invalidas'}, status=status.HTTP_401_UNAUTHORIZED)