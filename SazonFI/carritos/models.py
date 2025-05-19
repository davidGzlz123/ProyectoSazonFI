# carritos/models.py
from django.db import models
from django.conf import settings 
from productos.models import Producto # Asegurate que la ruta a tu modelo Producto sea correcta
from negocios.models import Negocio # Asegurate que la ruta a tu modelo Negocio sea correcta

class Carrito(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carrito' 
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        related_name='items' 
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, null=True, blank=True) 
    cantidad = models.PositiveIntegerField(default=1)
    precio_al_agregar = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 
    agregado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en carrito de {self.carrito.usuario.username}"

    def save(self, *args, **kwargs):
        if not self.precio_al_agregar and self.producto: 
            self.precio_al_agregar = self.producto.precio
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        if self.precio_al_agregar:
            return self.cantidad * self.precio_al_agregar
        elif self.producto and self.producto.precio: 
            return self.cantidad * self.producto.precio
        return 0

# --- MODELOS PARA PEDIDOS (DEFINIDOS EN LA APP 'carritos') ---

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PROCESANDO', 'Procesando'), 
        ('ENVIADO', 'Enviado'),       
        ('COMPLETADO', 'Completado'), 
        ('CANCELADO', 'Cancelado'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='pedidos_realizados')
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    total_pedido = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username if self.usuario else 'Usuario Eliminado'} - {self.estado}"

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items_pedido')
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='items_en_pedidos' 
    ) 
    negocio = models.ForeignKey(Negocio, on_delete=models.SET_NULL, null=True) 
    
    nombre_producto = models.CharField(max_length=255)
    precio_unitario_pedido = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField()
    subtotal_pedido = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.nombre_producto} (Pedido #{self.pedido.id})"

    def save(self, *args, **kwargs):
        self.subtotal_pedido = self.precio_unitario_pedido * self.cantidad
        super().save(*args, **kwargs)
