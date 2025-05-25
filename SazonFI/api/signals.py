from django.dispatch import receiver
from allauth.account.signals import user_signed_up

@receiver(user_signed_up)
def allauth_user_signed_up(request, user, **kwargs):
    """
    Esto se utiliza para asignar un rol por defecto al usuario cuando se registra usando allauth.
    En este caso, se asigna el rol 'cliente' al usuario.
    """
    user.rol = 'cliente'
    user.save()