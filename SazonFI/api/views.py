# api/views.py
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login 
from django.contrib.auth import logout as django_logout
from usuarios.models import Usuario 
from usuarios.serializers import UsuarioSerializer 
from rest_framework.views import APIView
from rest_framework import status
from negocios.models import Negocio
from negocios.serializers import NegocioSerializer
from django.db.models import Q


class RegistroUsuarioViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        serializer = UsuarioSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.save()
            # La contrase�a ya deberia estar hasheada por el serializador si usa create_user
            # o si el serializador llama a set_password.
            # Si no, esta bien aqui:
            # usuario.set_password(request.data['password']) 
            # usuario.save()
            # Es mejor que el serializador maneje la creacion completa y el hasheo.
            return Response({'message': 'Usuario registrado con exito'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InicioSesionAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password) # Pasar 'request' es buena practica
        
        if user is not None:
            # --- INICIO DE CAMBIO IMPORTANTE ---
            # Iniciar sesion de Django para que @login_required funcione
            login(request, user) 
            # --- FIN DE CAMBIO IMPORTANTE ---
            
            token, created = Token.objects.get_or_create(user=user)
            
            # Asegurarse de que 'rol' existe en tu modelo Usuario y obtenerlo de forma segura
            rol_usuario = getattr(user, 'rol', 'cliente') # 'cliente' como default si no tiene rol
            
            return Response({
                'token': token.key,
                'rol': rol_usuario,
                'user_id': user.pk, # Es util enviar el ID del usuario
                'username': user.username
            }, status=status.HTTP_200_OK)
        
        return Response({'error': 'Credenciales invalidas'}, status=status.HTTP_401_UNAUTHORIZED)
    
def get_queryset(self):
    query = self.request.GET.get('q', '').strip()
    categoria = self.request.GET.get('categoria', '').lower()
    orden = self.request.GET.get('orden', '').lower()

    queryset = Negocio.objects.all()

    if query:
        queryset = queryset.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(direccion__icontains=query) |
            Q(producto__nombre__icontains=query)
        ).distinct()

    if categoria in ['franquicia', 'estudiante']:
        queryset = queryset.filter(categoria=categoria)

    if orden == 'alfabetico':
        queryset = queryset.order_by('nombre')

    return queryset



class LogoutAPIView(APIView):
    """
    Vista para cerrar la sesión de Django del usuario autenticado.
    También invalida el token de DRF si se quisiera (aunque el logout de sesión es lo principal aquí).
    """
    permission_classes = [permissions.IsAuthenticated] # Solo usuarios autenticados pueden desloguearse

    def post(self, request, *args, **kwargs):
        try:
            # Opcional: Invalidar el token de DRF si lo estás usando y quieres que no se pueda reutilizar
            # request.user.auth_token.delete()
            pass # No borraremos el token por ahora, solo cerraremos la sesión de Django
        except Exception as e:
            # Manejar el caso donde el usuario no tenga un token (ej. solo sesión) o ya esté borrado
            print(f"Error al intentar borrar el token: {e}")
            pass

        django_logout(request) # Cierra la sesión de Django
        
        return Response({"detail": "Logout de sesión de Django exitoso."}, status=status.HTTP_200_OK)

