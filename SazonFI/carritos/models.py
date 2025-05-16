# carritos/models.py
from django.db import models
from django.conf import settings # Para obtener el AUTH_USER_MODEL
from productos.models import Producto # Asumiendo que tu modelo Producto está en la app 'productos'
from negocios.models import Negocio

class Carrito(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carrito' # Permite acceder al carrito desde el usuario: user.carrito
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        related_name='items' # Permite acceder a los items desde el carrito: carrito.items.all()
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    # Guarda referencia al negocio si es crucial para el item del carrito y no solo a través del producto
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_al_agregar = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # Opcional: para guardar el precio en ese momento
    agregado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en carrito de {self.carrito.usuario.username}"

    def save(self, *args, **kwargs):
        if not self.precio_al_agregar and self.producto: # Si no se especificó y hay producto, tomar el actual del producto
            self.precio_al_agregar = self.producto.precio
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        if self.precio_al_agregar:
            return self.cantidad * self.precio_al_agregar
        elif self.producto and self.producto.precio: # Fallback al precio actual del producto
            return self.cantidad * self.producto.precio
        return 0



class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PROCESANDO', 'Procesando'), # El negocio esta preparando el pedido
        ('ENVIADO', 'Enviado'),       # Si aplica (para productos fisicos)
        ('COMPLETADO', 'Completado'), # El cliente recibio/consumio el pedido
        ('CANCELADO', 'Cancelado'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='pedidos')
    # Guardamos una referencia al carrito original, aunque podria limpiarse despues
    # carrito_origen = models.ForeignKey(Carrito, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_generados')
    
    # Informacion del pedido
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    total_pedido = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    # Podrias anadir campos para direccion de envio, notas, etc., si es necesario

    def __str__(self):
        return f"Pedido #{self.id} - {self.usuario.username if self.usuario else 'Usuario Desconocido'} - {self.estado}"

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items_pedido')
    # CAMBIO: Anadido related_name para evitar conflicto
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='items_pedido_carritos_app' # Nombre unico para el acceso inverso desde Producto
    ) 
    negocio = models.ForeignKey(Negocio, on_delete=models.SET_NULL, null=True) # Guardar el negocio del producto en el momento del pedido
    
    # Guardar los detalles del producto en el momento del pedido, por si cambian despues
    nombre_producto = models.CharField(max_length=255)
    precio_unitario_pedido = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField()
    subtotal_pedido = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.nombre_producto} (Pedido #{self.pedido.id})"

    def save(self, *args, **kwargs):
        # Calcular subtotal antes de guardar
        self.subtotal_pedido = self.precio_unitario_pedido * self.cantidad
        super().save(*args, **kwargs)
